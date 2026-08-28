from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.message import create_message
from app.schemas.message import MessageCreate, MessageResponse
from app.models.message import Message
from app.models import User

from app.dependencies import get_current_user


router = APIRouter()


@router.post(
    "/messages",
    response_model=MessageResponse
)
async def create_message_endpoint(
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    message = await create_message(
        message_data,
        current_user.id,
        session
    )

    return message


@router.get(
    "/messages/received",
    response_model=list[MessageResponse]
)
async def get_received_messages(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message)
        .where(Message.recipient_id == current_user.id)
        .order_by(Message.created_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/messages/sent",
    response_model=list[MessageResponse]
)
async def get_sent_messages(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message)
        .where(Message.sender_id == current_user.id)
        .order_by(Message.created_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/messages/dialog/{recipient_id}",
    response_model=list[MessageResponse]
)
async def get_dialog(
    recipient_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    recipient_result = await session.execute(
        select(User).where(User.id == recipient_id)
    )

    recipient_user = recipient_result.scalar_one_or_none()

    if recipient_user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    result = await session.execute(
        select(Message).where(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == recipient_user.id),
                and_(Message.sender_id == recipient_user.id, Message.recipient_id == current_user.id),
            )
        ).order_by(Message.created_at.asc())
    )

    return result.scalars().all()


