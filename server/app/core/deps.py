"""FastAPI 依赖：OAuth2 令牌解析、当前用户、RBAC 角色校验。"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

# OAuth2 密码模式：Swagger 右上角 "Authorize" 会自动把 token 放进 Authorization 头
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_URL)

CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="身份凭证无效或已过期",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise CredentialsException

    username: str | None = payload.get("sub")
    if not username:
        raise CredentialsException

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise CredentialsException
    return user


def get_current_active_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """RBAC：只有 admin 角色可访问（如模型配置、用户管理）。"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：该操作仅管理员可用",
        )
    return current_user
