from fastapi import APIRouter, Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.message import create_message
from app.schemas.message import MessageCreate, MessageResponse
from app.models.message import Message


router = APIRouter()


@router.post(
    "/messages",
    response_model=MessageResponse
)
async def create_message_endpoint(
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session)
):
    message = await create_message(
        message_data,
        session
    )

    return message


@router.get(
    "/messages/received/{user_id}",
    response_model=list[MessageResponse]
)
async def get_received_messages(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message)
        .where(Message.recipient_id == user_id)
        .order_by(Message.created_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/messages/sent/{user_id}",
    response_model=list[MessageResponse]
)
async def get_sent_messages(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message)
        .where(Message.sender_id == user_id)
        .order_by(Message.created_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/messages/dialog/{user1}/{user2}",
    response_model=list[MessageResponse]
)
async def get_dialog(
    user1: int,
    user2: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message).where(
            or_(
                and_(Message.sender_id == user1, Message.recipient_id == user2),
                and_(Message.sender_id == user2, Message.recipient_id == user1),
            )
        ).order_by(Message.created_at.asc())
    )

    return result.scalars().all()
