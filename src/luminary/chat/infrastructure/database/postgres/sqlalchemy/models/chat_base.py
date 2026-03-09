from __future__ import annotations

from uuid import UUID

from common.infrastructure.database.sqlalchemy.models.base import Base
from sqlalchemy import Boolean, ColumnElement, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ChatSourceAssociation(Base):
    __tablename__ = "chat_sources"

    chat_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("chats.chat_id"), primary_key=True
    )
    source_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)


class ChatBase(Base):
    __tablename__ = "chats"

    chat_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(PGUUID, nullable=False)
    folder_id: Mapped[UUID | None] = mapped_column(PGUUID, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    assistant_id: Mapped[UUID | None] = mapped_column(PGUUID, nullable=True)
    model_id: Mapped[UUID] = mapped_column(PGUUID, nullable=False)
    max_context_messages: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    source_associations: Mapped[list[ChatSourceAssociation]] = relationship(
        "ChatSourceAssociation", lazy="noload"
    )

    @hybrid_property
    def is_active(self) -> bool:
        return not self.is_deleted

    @is_active.inplace.expression
    @classmethod
    def _is_active(cls) -> ColumnElement[bool]:
        return cls.is_deleted.is_not(True)
