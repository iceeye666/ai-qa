"""内置演示模型：无需任何 API Key，保证项目 clone 下来即可跑通全链路。

它会基于用户问题做规则化回答（关键词命中 + 兜底模板），并明确标注"演示模式"，
避免被误认为是真实大模型输出。真实接入后前端切换到 qwen/openai 即可。
"""

import asyncio
import re
from typing import AsyncIterator, List

from app.services.providers.base import BaseProvider, ChatMessage, ModelResult

RULES = [
    (
        r"(你好|hi|hello|哈喽|您好)",
        "你好！我是本地演示模型（Echo），当前没有配置任何大模型 API Key。\n"
        "管理员可在「模型配置」页填入通义千问 / OpenAI / ChatGLM 的 Key，"
        "或在服务端 .env 中配置 QWEN_API_KEY，即可切换为真实大模型。",
    ),
    (
        r"(fastapi|后端|接口|api)",
        "本项目后端采用 FastAPI：\n"
        "1) 自动生成 Swagger 文档（/docs），接口可在线调试；\n"
        "2) 依赖注入体系把数据库会话、当前用户、RBAC 权限统一收敛到 app/core/deps.py；\n"
        "3) Pydantic 模型做请求/响应校验，字段错误会返回 422 明细。",
    ),
    (
        r"(vue|前端|界面|页面)",
        "前端基于 Vue 3 + Vite：路由守卫拦截未登录访问，Axios 拦截器自动注入 "
        "Bearer Token，Pinia 管理用户态与模型列表，组件内实现对话流与模型切换。",
    ),
    (
        r"(jwt|oauth2|鉴权|认证|权限|token)",
        "认证流程：\n"
        "1) POST /api/v1/auth/login 用 OAuth2 Password Flow 提交表单；\n"
        "2) 服务端校验密码后签发 JWT（sub=用户名, role=角色）；\n"
        "3) 之后请求头带 Authorization: Bearer <token>；\n"
        "4) 依赖 get_current_user 解析 token，get_current_active_admin 做角色拦截。",
    ),
    (
        r"(模型|qwen|通义|chatglm|openai|切换)",
        "模型层是可插拔的：所有适配器继承 BaseProvider，实现 generate 即可。"
        "新增模型只需在 registry 注册 provider 名称，或在「模型配置」页新增一条记录，"
        "核心问答逻辑零改动。",
    ),
    (
        r"(部署|nginx|docker|启动)",
        "启动方式：后端 `uvicorn app.main:app --reload`；前端 `npm run dev`，"
        "打包后 `dist/` 直接丢到 Nginx 静态目录，并用 /api 反向代理到后端即可。",
    ),
]


class EchoProvider(BaseProvider):
    name = "echo"
    require_api_key = False

    def _answer(self, question: str) -> str:
        for pattern, answer in RULES:
            if re.search(pattern, question, re.IGNORECASE):
                return answer
        return (
            "【演示模式】未配置大模型 API Key，这是内置 Echo 模型的占位回答。\n\n"
            f"你问的是：{question}\n\n"
            "Echo 模型会把你的输入做结构化回显，用于验证「前端 → 后端 → 模型适配层 → 数据库」"
            "整条链路是否通畅。配置真实 Key 后将由对应大模型作答。"
        )

    async def generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> ModelResult:
        question = next((m.content for m in reversed(messages) if m.role == "user"), "")
        content = self._answer(question)
        return ModelResult(content=content, tokens=len(content) // 2)

    async def stream_generate(
        self, messages: List[ChatMessage], temperature: float = 0.7, **kwargs
    ) -> AsyncIterator[str]:
        question = next((m.content for m in reversed(messages) if m.role == "user"), "")
        content = self._answer(question)
        # 按标点切块模拟打字机效果
        for piece in re.findall(r"[\s\S]{1,12}", content):
            yield piece
            await asyncio.sleep(0.02)
