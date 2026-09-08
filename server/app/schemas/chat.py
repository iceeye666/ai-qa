from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """非流式问答请求。"""

    message: str = Field(..., min_length=1, description="用户提问")
    conversation_id: Optional[int] = Field(default=None, description="会话 ID，为空则自动新建")
    model_key: Optional[str] = Field(default=None, description="模型 key，为空则用系统默认模型")
    system_prompt: Optional[str] = Field(default=None, description="可选的系统人设提示词")
    history_rounds: int = Field(default=8, ge=0, le=50, description="携带的历史对话轮数")


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    model_key: str
    model_name: str
    answer: str
    tokens: int
    latency_ms: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model_key: str
    tokens: int
    latency_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    model_key: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []


class ConversationCreate(BaseModel):
    title: str = "新对话"
    model_key: Optional[str] = None


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
