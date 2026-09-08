"""用户管理：仅管理员可访问（RBAC）。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=List[UserOut], summary="用户列表（管理员）")
def list_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=201, summary="创建用户（管理员）")
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if payload.role not in (UserRole.ADMIN.value, UserRole.USER.value):
        raise HTTPException(status_code=400, detail="角色取值非法")
    user = User(
        username=payload.username,
        nickname=payload.nickname or payload.username,
        hashed_password=get_password_hash(payload.password),
        role=UserRole(payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut, summary="修改用户（管理员）")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = get_password_hash(data.pop("password"))
    if "role" in data and data["role"]:
        if data["role"] not in (UserRole.ADMIN.value, UserRole.USER.value):
            raise HTTPException(status_code=400, detail="角色取值非法")
        user.role = UserRole(data["role"])
    for key in ("nickname", "is_active"):
        if key in data and data[key] is not None:
            setattr(user, key, data[key])
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204, summary="删除用户（管理员）")
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
