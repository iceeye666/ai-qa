"""问答接口：非流式 / 流式两种模式。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ask, stream_ask
from app.services.providers.base import ProviderError

router = APIRouter(prefix="/chat", tags=["问答"])


@router.post("", response_model=ChatResponse, summary="发起一次问答")
async def chat(
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        conv, assistant_msg, config, latency_ms = await ask(
            db,
            user_id=current_user.id,
            question=payload.message,
            model_key=payload.model_key,
            conversation_id=payload.conversation_id,
            system_prompt=payload.system_prompt,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        model_key=config.key,
        model_name=config.name,
        answer=assistant_msg.content,
        tokens=assistant_msg.tokens,
        latency_ms=latency_ms,
    )


@router.post("/stream", summary="流式问答（SSE）")
async def chat_stream(
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    async def event_gen():
        async for event in stream_ask(
            db,
            user_id=current_user.id,
            question=payload.message,
            model_key=payload.model_key,
            conversation_id=payload.conversation_id,
            system_prompt=payload.system_prompt,
        ):
            yield event

    return EventSourceResponse(event_gen())
