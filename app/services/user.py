from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.user import UserCreate
from app.security import hash_password


async def create_user(
    user_data: UserCreate,
    session: AsyncSession,
) -> User:

    password_hash = hash_password(user_data.password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash
    )
    
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user