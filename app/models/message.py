from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

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
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    text: Mapped[str] = mapped_column(
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id],
        back_populates="sent_messages"
    )
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id],
        back_populates="received_messages"
    )
