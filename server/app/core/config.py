"""全局配置：全部支持环境变量覆盖，方便本地开发 / 服务器部署切换。"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---------- 基础 ----------
    APP_NAME: str = "AI 智能问答平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ---------- 数据库 ----------
    # 默认使用 SQLite，零配置启动；生产可改为 mysql+pymysql://user:pwd@host:3306/db
    DATABASE_URL: str = "sqlite:///./ai_qa.db"

    # ---------- 安全 / JWT + OAuth2 ----------
    SECRET_KEY: str = "please-change-this-secret-key-in-production-0a1b2c3d4e5f"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 小时
    # OAuth2 密码模式约定的 token 端点
    TOKEN_URL: str = "/api/v1/auth/login"

    # ---------- CORS ----------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8085"

    # ---------- 模型适配 ----------
    # 未配置任何真实模型 Key 时，自动回退到内置 Echo 演示模型，保证项目开箱可跑
    DEFAULT_MODEL: str = "qwen-plus"
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    CHATGLM_API_KEY: str = ""
    CHATGLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    REQUEST_TIMEOUT: int = 60

    # ---------- 初始化账号 ----------
    INIT_ADMIN_USERNAME: str = "admin"
    INIT_ADMIN_PASSWORD: str = "admin123"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
