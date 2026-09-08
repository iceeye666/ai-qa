"""认证相关接口：注册、OAuth2 登录、获取当前用户信息。"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse, summary="用户登录（OAuth2 密码模式）")
def login(form_data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    """Swagger 右上角 Authorize 直接可用；也支持前端以 JSON 提交。"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    token = create_access_token(subject=user.username, role=user.role.value)
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        username=user.username,
    )


@router.post("/register", response_model=UserOut, status_code=201, summary="注册普通用户")
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=payload.username,
        nickname=payload.nickname or payload.username,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut, summary="获取当前登录用户")
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserOut.model_validate(current_user)
