from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base



if TYPE_CHECKING:
    from .user import User


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    text: Mapped[str] = mapped_column(
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    sender: Mapped["User"] = relationship(
        back_populates="messages"
    )