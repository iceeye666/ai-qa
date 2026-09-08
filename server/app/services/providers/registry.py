"""模型适配器注册表 + 工厂。

新增模型：写一个 BaseProvider 子类，然后加到 PROVIDER_CLASSES 即可。
"""

from typing import Dict, List, Type

from app.core.config import settings
from app.models.model_config import ModelConfig
from app.services.providers.base import BaseProvider
from app.services.providers.echo import EchoProvider
from app.services.providers.openai_compatible import (
    ChatGLMProvider,
    OpenAIProvider,
    QwenProvider,
)

PROVIDER_CLASSES: Dict[str, Type[BaseProvider]] = {
    EchoProvider.name: EchoProvider,
    QwenProvider.name: QwenProvider,
    OpenAIProvider.name: OpenAIProvider,
    ChatGLMProvider.name: ChatGLMProvider,
}

# provider -> 默认 base_url（模型中未填 base_url 时使用）
DEFAULT_BASE_URL: Dict[str, str] = {
    "qwen": settings.QWEN_BASE_URL,
    "openai": settings.OPENAI_BASE_URL,
    "chatglm": settings.CHATGLM_BASE_URL,
}

# provider -> 环境变量兜底 Key
DEFAULT_API_KEY: Dict[str, str] = {
    "qwen": settings.QWEN_API_KEY,
    "openai": settings.OPENAI_API_KEY,
    "chatglm": settings.CHATGLM_API_KEY,
}


def list_providers() -> List[Dict]:
    return [
        {
            "provider": name,
            "require_api_key": cls.require_api_key,
            "default_base_url": DEFAULT_BASE_URL.get(name, ""),
            "description": (cls.__doc__ or "").strip().split("\n")[0],
        }
        for name, cls in PROVIDER_CLASSES.items()
    ]


def build_provider(config: ModelConfig) -> BaseProvider:
    """由数据库里的 ModelConfig 记录构造适配器实例。"""
    provider_name = (config.provider or "echo").lower()
    cls = PROVIDER_CLASSES.get(provider_name)
    if cls is None:
        # 未知 provider 直接降级为 echo，避免整个问答链路挂掉
        cls = EchoProvider
        provider_name = "echo"

    api_key = config.api_key or DEFAULT_API_KEY.get(provider_name, "")
    base_url = config.base_url or DEFAULT_BASE_URL.get(provider_name, "")

    return cls(
        model_name=config.model_name or config.key,
        api_key=api_key,
        base_url=base_url,
        timeout=settings.REQUEST_TIMEOUT,
    )
