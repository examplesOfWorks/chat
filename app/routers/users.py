from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user import create_user

from sqlalchemy.exc import IntegrityError


router = APIRouter()

@router.get(
    "/users",
    response_model=list[UserResponse]
    )
async def get_users(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(User)
    )

    users = result.scalars().all()

    return users


@router.get(
    "/users/search",
    response_model=list[UserResponse]
)
async def search_users(
    username: str,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(User).where(
            User.username.ilike(f"%{username}%")
        )
    )

    users = result.scalars().all()

    return users


@router.get(
    "/users/{user_id}",
    response_model= UserResponse
)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.post(
    "/users",
    response_model=UserResponse,
)
async def create_user_endpoint(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await create_user(
            user_data,
            session
        )

        return user
    
    except IntegrityError:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )