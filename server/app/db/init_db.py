"""建表 + 初始化种子数据（管理员账号 & 默认模型列表）。"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base, SessionLocal, engine
from app.models.conversation import Conversation, Message  # noqa: F401
from app.models.model_config import ModelConfig
from app.models.user import User, UserRole

SEED_MODELS = [
    {
        "key": "qwen-plus",
        "name": "通义千问 Plus",
        "provider": "qwen",
        "model_name": "qwen-plus",
        "description": "阿里云百炼（DashScope 兼容模式）主力模型，需在 .env 或配置页填写 QWEN_API_KEY",
    },
    {
        "key": "qwen-turbo",
        "name": "通义千问 Turbo",
        "provider": "qwen",
        "model_name": "qwen-turbo",
        "description": "响应速度更快、成本更低的通义千问版本",
    },
    {
        "key": "gpt-4o-mini",
        "name": "OpenAI GPT-4o mini",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "description": "需配置 OPENAI_API_KEY，支持海外访问场景",
    },
    {
        "key": "glm-4-flash",
        "name": "智谱 GLM-4-Flash",
        "provider": "chatglm",
        "model_name": "glm-4-flash",
        "description": "需配置 CHATGLM_API_KEY，智谱开放平台 v4 协议",
    },
    {
        "key": "echo-demo",
        "name": "本地演示模型",
        "provider": "echo",
        "model_name": "echo-demo",
        "description": "无需 API Key 的内置模型，用于验证链路；未配置任何 Key 时自动兜底",
    },
]


def seed_models(db: Session) -> None:
    for item in SEED_MODELS:
        exists = db.query(ModelConfig).filter(ModelConfig.key == item["key"]).first()
        if not exists:
            db.add(ModelConfig(**item))
    db.commit()


def seed_admin(db: Session) -> None:
    exists = db.query(User).filter(User.username == settings.INIT_ADMIN_USERNAME).first()
    if not exists:
        db.add(
            User(
                username=settings.INIT_ADMIN_USERNAME,
                nickname="系统管理员",
                hashed_password=get_password_hash(settings.INIT_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            )
        )
        db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        seed_admin(db)
        seed_models(db)
    finally:
        db.close()
