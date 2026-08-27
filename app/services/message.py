from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, User
from app.schemas.message import MessageCreate



async def create_message(
    message_data: MessageCreate,
    user_id: int,
    session: AsyncSession
) -> Message:

    result = await session.execute(
        select(User).where(User.id == message_data.recipient_id)
    )

    recipient = result.scalar_one_or_none()

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    message = Message(
        sender_id=user_id,
        recipient_id=message_data.recipient_id,
        text=message_data.text
    )

    session.add(message)

    await session.commit()
    await session.refresh(message)

    return message