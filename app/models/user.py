from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .message import Message

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    username: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(
        nullable=True
    )
    email: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="sender"
    )