"""模型配置：查询对所有登录用户开放，增删改仅管理员（RBAC）。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_admin, get_current_user
from app.db.session import get_db
from app.models.model_config import ModelConfig
from app.models.user import User
from app.schemas.model import (
    ModelConfigCreate,
    ModelConfigOut,
    ModelConfigUpdate,
)
from app.services.providers.registry import list_providers

router = APIRouter(prefix="/models", tags=["模型配置"])


def _to_out(cfg: ModelConfig) -> ModelConfigOut:
    data = ModelConfigOut.model_validate(cfg)
    data.has_api_key = bool(cfg.api_key)
    return data


@router.get("", response_model=List[ModelConfigOut], summary="可用模型列表")
def list_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    cfgs = db.query(ModelConfig).filter(ModelConfig.is_active.is_(True)).all()
    return [_to_out(c) for c in cfgs]


@router.get("/providers", summary="支持的模型适配器")
def providers(current_user: Annotated[User, Depends(get_current_user)]):
    return list_providers()


@router.post("", response_model=ModelConfigOut, status_code=201, summary="新增模型（管理员）")
def create_model(
    payload: ModelConfigCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    if db.query(ModelConfig).filter(ModelConfig.key == payload.key).first():
        raise HTTPException(status_code=400, detail="模型 key 已存在")
    cfg = ModelConfig(**payload.model_dump())
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)


@router.put("/{model_id}", response_model=ModelConfigOut, summary="修改模型（管理员）")
def update_model(
    model_id: int,
    payload: ModelConfigUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    cfg = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="模型不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)


@router.delete("/{model_id}", status_code=204, summary="删除模型（管理员）")
def delete_model(
    model_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_active_admin)],
):
    cfg = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="模型不存在")
    db.delete(cfg)
    db.commit()
