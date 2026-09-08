"""问答业务编排：负责模型选择、上下文组装、调用适配器、落库。"""

import time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.models.model_config import ModelConfig
from app.services.providers.base import ChatMessage, ProviderError
from app.services.providers.registry import build_provider

DEFAULT_SYSTEM_PROMPT = "你是企业智能问答助手，回答请简洁、准确、结构化。"


def resolve_model(db: Session, model_key: Optional[str]) -> ModelConfig:
    """选择模型：指定 key -> 默认 key -> 第一条可用记录 -> 内置 Echo 兜底。

    这样即使上游模型不可用，问答链路也不会中断（自动降级到演示模型）。
    """
    config: Optional[ModelConfig] = None
    if model_key:
        config = db.query(ModelConfig).filter(ModelConfig.key == model_key).first()
        if config is None:
            raise ProviderError(f"模型 {model_key} 不存在")
        if not config.is_active:
            raise ProviderError(f"模型 {model_key} 已被停用")
    else:
        config = (
            db.query(ModelConfig)
            .filter(ModelConfig.key == settings.DEFAULT_MODEL, ModelConfig.is_active.is_(True))
            .first()
            or db.query(ModelConfig).filter(ModelConfig.is_active.is_(True)).first()
        )

    if config is None:
        config = ModelConfig(
            key="echo-demo",
            name="本地演示模型",
            provider="echo",
            model_name="echo-demo",
            is_active=True,
        )

    provider = build_provider(config)
    if not provider.is_available():
        # 未配置 Key -> 回退到内置演示模型，保证功能可用并给出提示
        config = (
            db.query(ModelConfig).filter(ModelConfig.provider == "echo").first()
            or ModelConfig(
                key="echo-demo",
                name="本地演示模型",
                provider="echo",
                model_name="echo-demo",
                is_active=True,
            )
        )
    return config


def get_or_create_conversation(
    db: Session, user_id: int, conversation_id: Optional[int], model_key: str, question: str
) -> Conversation:
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if conv is None:
            raise PermissionError("会话不存在或无权访问")
        conv.model_key = model_key
        return conv

    conv = Conversation(
        user_id=user_id,
        title=question.strip()[:30] or "新对话",
        model_key=model_key,
    )
    db.add(conv)
    db.flush()
    return conv


def build_context(
    db: Session, conversation: Optional[Conversation], question: str, system_prompt: Optional[str]
) -> List[ChatMessage]:
    messages: List[ChatMessage] = [
        ChatMessage(role="system", content=system_prompt or DEFAULT_SYSTEM_PROMPT)
    ]
    if conversation is not None:
        history = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.id.asc())
            .limit(20)
            .all()
        )
        messages.extend(ChatMessage(role=m.role, content=m.content) for m in history)
    messages.append(ChatMessage(role="user", content=question))
    return messages


async def ask(
    db: Session,
    user_id: int,
    question: str,
    model_key: Optional[str] = None,
    conversation_id: Optional[int] = None,
    system_prompt: Optional[str] = None,
):
    """执行一次问答：写用户消息 -> 调模型 -> 写助手消息 -> 返回。"""
    config = resolve_model(db, model_key)
    conv = get_or_create_conversation(db, user_id, conversation_id, config.key, question)

    user_msg = Message(
        conversation_id=conv.id, role="user", content=question, model_key=config.key
    )
    db.add(user_msg)
    db.flush()

    messages = build_context(db, conv, question, system_prompt)

    provider = build_provider(config)
    start = time.perf_counter()
    result = await provider.generate(messages)
    latency_ms = int((time.perf_counter() - start) * 1000)

    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=result.content,
        model_key=config.key,
        tokens=result.tokens,
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return conv, assistant_msg, config, latency_ms


async def stream_ask(
    db: Session,
    user_id: int,
    question: str,
    model_key: Optional[str] = None,
    conversation_id: Optional[int] = None,
    system_prompt: Optional[str] = None,
):
    """流式问答：先 yield 元信息，再逐块 yield 文本，最后 yield 完成事件并落库。"""
    import json

    config = resolve_model(db, model_key)
    conv = get_or_create_conversation(db, user_id, conversation_id, config.key, question)

    user_msg = Message(
        conversation_id=conv.id, role="user", content=question, model_key=config.key
    )
    db.add(user_msg)
    db.flush()
    db.commit()

    yield {
        "event": "meta",
        "data": json.dumps(
            {"conversation_id": conv.id, "model_key": config.key, "model_name": config.name},
            ensure_ascii=False,
        ),
    }

    messages = build_context(db, conv, question, system_prompt)
    provider = build_provider(config)

    start = time.perf_counter()
    pieces: List[str] = []
    try:
        async for chunk in provider.stream_generate(messages):
            pieces.append(chunk)
            yield {"event": "delta", "data": json.dumps({"content": chunk}, ensure_ascii=False)}
    except ProviderError as exc:
        yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
        return

    latency_ms = int((time.perf_counter() - start) * 1000)
    content = "".join(pieces)
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=content,
        model_key=config.key,
        tokens=len(content) // 2,
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    db.commit()

    yield {
        "event": "done",
        "data": json.dumps(
            {"message_id": assistant_msg.id, "tokens": assistant_msg.tokens, "latency_ms": latency_ms},
            ensure_ascii=False,
        ),
    }
