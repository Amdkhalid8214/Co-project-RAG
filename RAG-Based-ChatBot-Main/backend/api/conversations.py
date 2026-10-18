from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload

from backend.db.session import get_db
from backend.db.models import ConversationModel, MessageModel, UserModel
from backend.api.auth import get_current_user_optional

router = APIRouter(prefix="/conversations", tags=["conversations"])

class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field("New Chat", max_length=255)

class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

@router.get("")
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    stmt = select(ConversationModel)
    if current_user and current_user.role != "admin":
        # Strict user isolation
        stmt = stmt.where(ConversationModel.user_id == current_user.id)
    elif not current_user:
        stmt = stmt.where(ConversationModel.user_id.is_(None))
    stmt = stmt.order_by(desc(ConversationModel.updated_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    convs = result.scalars().all()
    return [c.to_dict() for c in convs]

@router.post("")
async def create_conversation(
    req: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    new_conv = ConversationModel(
        title=req.title.strip() if req.title else "New Chat",
        user_id=user_id
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return new_conv.to_dict()

@router.get("/{conv_id}")
async def get_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    stmt = (
        select(ConversationModel)
        .where(ConversationModel.id == conv_id)
        .options(selectinload(ConversationModel.messages))
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user and current_user.role != "admin" and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")

    data = conv.to_dict()
    data["messages"] = [m.to_dict() for m in conv.messages]
    return data

@router.patch("/{conv_id}")
async def update_conversation(
    conv_id: str,
    req: UpdateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user and current_user.role != "admin" and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to modify this conversation")

    conv.title = req.title.strip() or "Untitled"
    await db.commit()
    return conv.to_dict()

@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user and current_user.role != "admin" and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to delete this conversation")

    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted", "id": conv_id}

