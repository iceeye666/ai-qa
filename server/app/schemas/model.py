from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ModelConfigOut(BaseModel):
    id: int
    key: str
    name: str
    provider: str
    model_name: str
    base_url: str
    description: str
    is_active: bool
    has_api_key: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ModelConfigCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=64, description="唯一标识，如 qwen-plus")
    name: str = Field(..., min_length=1, max_length=64, description="展示名称")
    provider: str = Field(..., description="适配器：qwen / openai / chatglm / echo")
    model_name: str = Field(default="", description="上游真实模型名")
    base_url: str = ""
    api_key: str = ""
    description: str = ""
    is_active: bool = True


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
