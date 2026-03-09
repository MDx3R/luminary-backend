from __future__ import annotations

from datetime import datetime
from uuid import UUID

from common.infrastructure.database.sqlalchemy.models.base import Base
from sqlalchemy import Boolean, ColumnElement, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FolderChatAssociation(Base):
    __tablename__ = "folder_chats"

    folder_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("folders.folder_id"), primary_key=True
    )
    chat_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)


class FolderSourceAssociation(Base):
    __tablename__ = "folder_sources"

    folder_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("folders.folder_id"), primary_key=True
    )
    source_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)


class FolderBase(Base):
    __tablename__ = "folders"

    folder_id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(PGUUID, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    assistant_id: Mapped[UUID | None] = mapped_column(PGUUID, nullable=True)
    editor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    editor_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    chat_associations: Mapped[list[FolderChatAssociation]] = relationship(
        "FolderChatAssociation", lazy="noload"
    )
    source_associations: Mapped[list[FolderSourceAssociation]] = relationship(
        "FolderSourceAssociation", lazy="noload"
    )

    @hybrid_property
    def is_active(self) -> bool:
        return not self.is_deleted

    @is_active.inplace.expression
    @classmethod
    def _is_active(cls) -> ColumnElement[bool]:
        return cls.is_deleted.is_not(True)
