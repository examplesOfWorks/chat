import jwt

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.security import decode_access_token, SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login"
)

 
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    user_id = decode_access_token(token)

    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден",
        )

    return user


async def get_current_web_user(
    access_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session)
) -> User:

    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не авторизован"
        )

    try:
        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
            status_code=401,
            detail="Недействительный токен"
        )

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Некорректный токен",
        )

    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден",
        )

    return user