"""OpenAI 协议兼容适配器基类。

通义千问（DashScope 兼容模式）、OpenAI、智谱 ChatGLM(v4) 都实现了 OpenAI 的
/v1/chat/completions 协议，因此共用一套 HTTP 调用逻辑，只改 base_url 与模型名即可。
"""

import json
from typing import Any, AsyncIterator, Dict, List

import httpx

from app.services.providers.base import (
    BaseProvider,
    ChatMessage,
    ModelResult,
    ProviderError,
)


class OpenAICompatibleProvider(BaseProvider):
    require_api_key = True

    def _endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self, messages: List[ChatMessage], temperature: float, stream: bool, **kwargs
    ) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": stream,
            **kwargs,
        }

    async def generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> ModelResult:
        if not self.is_available():
            raise ProviderError(self.unavailable_reason() or "模型不可用")
        payload = self._build_payload(messages, temperature, stream=False, **kwargs)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self._endpoint(), headers=self._headers(), json=payload)
        if resp.status_code != 200:
            raise ProviderError(
                f"上游返回 {resp.status_code}: {resp.text[:300]}"
            )
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - 上游异常结构
            raise ProviderError(f"解析上游响应失败: {data}") from exc
        usage = data.get("usage") or {}
        return ModelResult(
            content=content or "",
            tokens=int(usage.get("total_tokens") or 0),
            raw=data,
        )

    async def stream_generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> AsyncIterator[str]:
        if not self.is_available():
            raise ProviderError(self.unavailable_reason() or "模型不可用")
        payload = self._build_payload(messages, temperature, stream=True, **kwargs)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", self._endpoint(), headers=self._headers(), json=payload
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise ProviderError(f"上游返回 {resp.status_code}: {body[:300]}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta") or {}
                        if delta.get("content"):
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class QwenProvider(OpenAICompatibleProvider):
    """通义千问（阿里云百炼 DashScope 兼容模式）。"""

    name = "qwen"


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"


class ChatGLMProvider(OpenAICompatibleProvider):
    """智谱 GLM-4 系列，同样兼容 OpenAI 协议。"""

    name = "chatglm"
