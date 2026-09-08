"""会话（对话记录）管理：列表 / 详情 / 新建 / 重命名 / 删除。"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    ConversationRename,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["会话"])


def _to_out(db: Session, conv: Conversation) -> ConversationOut:
    count = db.query(Message).filter(Message.conversation_id == conv.id).count()
    data = ConversationOut.model_validate(conv)
    data.message_count = count
    return data


@router.get("", response_model=List[ConversationOut], summary="我的会话列表")
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    keyword: str = Query(default="", description="按标题模糊搜索"),
):
    # 数据隔离：普通用户只能看到自己的会话
    q = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    if keyword:
        q = q.filter(Conversation.title.like(f"%{keyword}%"))
    convs = q.order_by(Conversation.updated_at.desc()).all()
    return [_to_out(db, c) for c in convs]


@router.post("", response_model=ConversationOut, status_code=201, summary="新建会话")
def create_conversation(
    payload: ConversationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title,
        model_key=payload.model_key or "",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _to_out(db, conv)


@router.get("/{conversation_id}", response_model=ConversationDetail, summary="会话详情（含消息）")
def get_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    detail = ConversationDetail.model_validate(conv)
    detail.messages = [MessageOut.model_validate(m) for m in conv.messages]
    return detail


@router.patch("/{conversation_id}", response_model=ConversationOut, summary="重命名会话")
def rename_conversation(
    conversation_id: int,
    payload: ConversationRename,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    conv.title = payload.title
    db.commit()
    db.refresh(conv)
    return _to_out(db, conv)


@router.delete("/{conversation_id}", status_code=204, summary="删除会话")
def delete_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(conv)
    db.commit()
