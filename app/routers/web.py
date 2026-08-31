from pathlib import Path
import jwt

from fastapi import APIRouter, Depends, Form, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.models.message import Message
from app.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.dependencies import get_current_web_user

from app.schemas.message import MessageCreate
from app.services.message import create_message
from app.services.websocket import manager



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


@router.get("/chat", response_class=HTMLResponse, include_in_schema=False)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_web_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(User)
        .where(User.id != current_user.id)
        .order_by(User.username)
    )

    users = result.scalars().all()

    return templates.TemplateResponse(
        name="chat.html",
        request=request,
        context={
            "request": request,
            "user": current_user,
            "users": users
        }
    )


@router.get("/chat/{recipient_id}", response_class=HTMLResponse, include_in_schema=False)
async def dialog_page(
    request: Request,
    recipient_id: int,
    current_user: User = Depends(get_current_web_user),
    session: AsyncSession = Depends(get_session),
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

    messages = result.scalars().all()

    return templates.TemplateResponse(
        name="dialog.html",
        request=request,
        context={
            "request": request,
            "user": current_user,
            "recipient": recipient_user,
            "messages": messages
        }
    )

@router.post(
    "/chat/{recipient_id}/send"
)
async def send_message_from_web(
    recipient_id: int,
    text: str = Form(...),
    current_user: User = Depends(get_current_web_user),
    session: AsyncSession = Depends(get_session),
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

    message_data = MessageCreate(
        sender_id=current_user.id,
        recipient_id=recipient_user.id,
        text=text
    )

    await create_message(
        message_data=message_data,
        user_id=current_user.id,
        session=session
    )

    return RedirectResponse(
        f"/web/chat/{recipient_id}",
        status_code=303
    )

# @router.websocket("/ws/chat/{recipient_id}")
# async def websocket_chat(
#     websocket: WebSocket,
#     recipient_id: int,
#     session: AsyncSession = Depends(get_session)
# ):
#     token = websocket.cookies.get("access_token")

#     if token is None:
#         await websocket.close(code=1008)
#         return

#     await websocket.accept()

#     try:
#         while True:
#             text = await websocket.receive_text()

#             await websocket.send_text(
#                 f"Сервер получил {text}"
#             )

#     except WebSocketDisconnect:
#         print("WebSocket отключен")

@router.websocket("/ws/chat/{recipient_id}")
async def websocket_chat(
    websocket: WebSocket,
    recipient_id: int,
    session: AsyncSession = Depends(get_session)
):
    token = websocket.cookies.get("access_token")

    if token is None:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload.get("sub"))

    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=1008)
        return

    current_result = await session.execute(
        select(User).where(User.id == user_id)
    )

    current_user = current_result.scalar_one_or_none()

    if current_user is None:
        await websocket.close(code=1008)
        return

    await manager.connect(current_user.id, websocket)

    recipient_online = manager.is_online(recipient_id)

    await manager.send_to_user(
        current_user.id,
        {
            "type": "user_status",
            "user_id": recipient_id,
            "status": "online" if recipient_online else "offline"
        }
    )

    await manager.send_to_user(
        recipient_id,
        {
            "type": "user_status",
            "user_id": current_user.id,
            "status": "online"
        }
    )

    try:
        while True:
            data = await websocket.receive_json()

            event_type = data.get("type")

            if event_type == "send_message":
                text = data.get("text", "").strip()

                if not text:
                    continue

                message_data = MessageCreate(
                    sender_id=current_user.id,
                    recipient_id=recipient_id,
                    text=text
                )

                message = await create_message(
                    message_data=message_data,
                    user_id=current_user.id,
                    session=session
                )

                event = {
                    "type": "new_message",
                    "message": {
                        "id": message.id,
                        "sender_id": message.sender_id,
                        "recipient_id": message.recipient_id,
                        "text": message.text,
                        "created_at": message.created_at.isoformat()
                    }
                }

                await manager.send_to_user(
                    recipient_id,
                    event
                )

                await manager.send_to_user(
                    current_user.id,
                    event
                )

            elif event_type == "typing_start":
                await manager.send_to_user(
                    recipient_id,
                    {
                        "type": "typing",
                        "user_id": current_user.id,
                        "is_typing": True
                    }
                )
            elif event_type == "typing_stop":
                await manager.send_to_user(
                    recipient_id,
                    {
                        "type": "typing",
                        "user_id": current_user.id,
                        "is_typing": False
                    }
                )
            elif event_type == "read":
                pass


    except WebSocketDisconnect:

        is_offline = manager.disconnect(current_user.id, websocket)

        if is_offline:
            await manager.send_to_user(
                recipient_id,
                {
                    "type": "user_status",
                    "user_id": current_user.id,
                    "status": "offline"
                }
            )
            print("WebSocket отключен")