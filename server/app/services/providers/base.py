"""模型适配层统一抽象。

新增一个大模型只需要两步：
1. 继承 BaseProvider 实现 generate / stream_generate；
2. 在 registry 中注册 provider 名称。
业务代码（chat_service / API）完全不需要改动 —— 这就是"可插拔"。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional


@dataclass
class ChatMessage:
    role: str  # system / user / assistant
    content: str


@dataclass
class ModelResult:
    content: str
    tokens: int = 0
    raw: Dict = field(default_factory=dict)


class ProviderError(Exception):
    """模型调用失败。"""


class BaseProvider(ABC):
    """所有模型适配器的父类。"""

    #: 注册表里的唯一 provider 名称
    name: str = "base"
    #: 是否必须配置 api_key 才可用
    require_api_key: bool = True

    def __init__(
        self,
        model_name: str,
        api_key: str = "",
        base_url: str = "",
        timeout: int = 60,
        **kwargs,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @abstractmethod
    async def generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> ModelResult:
        """一次性返回完整答案。"""

    async def stream_generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> AsyncIterator[str]:
        """流式输出；默认降级为一次性返回。"""
        result = await self.generate(messages, temperature=temperature, **kwargs)
        yield result.content

    def is_available(self) -> bool:
        return (not self.require_api_key) or bool(self.api_key)

    def unavailable_reason(self) -> Optional[str]:
        if self.require_api_key and not self.api_key:
            return f"模型 {self.model_name} 未配置 API Key"
        return None
