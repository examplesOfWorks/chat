from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.security import verify_password, create_access_token
from app.dependencies import get_current_web_user

router = APIRouter(prefix="/web", tags=["web"])

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        name="login.html",
        request=request
    )


@router.post("/login")
async def web_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(User).where(User.username == username)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is None or not verify_password(
        password,
        existing_user.password_hash
    ):
        return templates.TemplateResponse(
            name="login.html",
            status_code=401,
            request=request,
            context={
                "error": "Неверное имя пользователя или пароль"
            }
        )

    access_token = create_access_token(existing_user.id)

    response = RedirectResponse(
        "/web/chat",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True
    )

    return response

    # return {
    #     "access_token": access_token,
    #     "token_type": "bearer"
    # }


@router.get("/chat", response_class=HTMLResponse, include_in_schema=False)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_web_user),
):

    return templates.TemplateResponse(
        name="chat.html",
        request=request,
        context={
            "user": current_user
        }
    )