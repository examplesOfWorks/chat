from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message
from app.schemas.message import MessageCreate


async def create_message(
    message_data: MessageCreate,
    session: AsyncSession
) -> Message:

    message = Message(
        sender_id=message_data.sender_id,
        recipient_id=message_data.recipient_id,
        text=message_data.text
    )

    session.add(message)

    await session.commit()
    await session.refresh(message)

    return message