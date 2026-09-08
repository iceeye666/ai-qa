from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ModelConfig(Base):
    """可插拔模型注册表：每条记录对应一个可被前端切换的模型。

    provider 决定调用哪个适配器（qwen / openai / chatglm / echo），
    model_name 为传给上游服务的真实模型名。
    """

    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="echo")
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    base_url: Mapped[str] = mapped_column(String(255), default="")
    api_key: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
