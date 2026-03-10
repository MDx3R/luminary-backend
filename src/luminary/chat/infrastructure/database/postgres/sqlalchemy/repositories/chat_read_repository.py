"""Read repository implementation for Chat: ORM -> read models (cross-BC)."""

from collections.abc import Sequence
from uuid import UUID

from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from sqlalchemy import select
from sqlalchemy.orm import joinedload, with_polymorphic

from luminary.assistant.infrastructure.database.postgres.sqlalchemy.models.assistant_base import (
    AssistantBase,
)
from luminary.chat.application.dtos.read_models import (
    AttachmentReadModel,
    ChatReadModel,
    ChatSourceItem,
    ChatSummaryReadModel,
    MessageReadModel,
)
from luminary.chat.application.interfaces.repositories.chat_read_repository import (
    IChatReadRepository,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.chat_base import (
    ChatBase,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.message_base import (
    MessageBase,
)
from luminary.source.infrastructure.database.postgres.sqlalchemy.models.source_base import (
    SourceBase,
)


class ChatReadRepository(IChatReadRepository):
    def __init__(self, executor: QueryExecutor) -> None:
        self._executor = executor

    async def get_by_id(self, chat_id: UUID, owner_id: UUID) -> ChatReadModel:
        stmt = (
            select(ChatBase)
            .where(ChatBase.chat_id == chat_id)
            .where(ChatBase.owner_id == owner_id)
            .where(ChatBase.is_active)
            .options(joinedload(ChatBase.source_associations))
        )
        chat = await self._executor.execute_scalar_one(stmt)
        if not chat:
            raise NotFoundError(str(chat_id))

        assistant_name: str | None = None
        if chat.assistant_id:
            astmt = (
                select(AssistantBase.name)
                .where(AssistantBase.assistant_id == chat.assistant_id)
                .where(AssistantBase.is_active)
            )
            assistant_name = await self._executor.execute_scalar_one(astmt)

        source_ids = [a.source_id for a in chat.source_associations]
        sources_list: list[ChatSourceItem] = []
        if source_ids:
            poly = with_polymorphic(SourceBase, "*")
            sstmt = (
                select(poly).where(poly.source_id.in_(source_ids)).where(poly.is_active)
            )
            source_rows = await self._executor.execute_scalar_many(sstmt)
            id_to_source = {r.source_id: r for r in source_rows}
            for sid in source_ids:
                s = id_to_source.get(sid)
                if s:
                    sources_list.append(
                        ChatSourceItem(
                            id=s.source_id,
                            title=s.title,
                            type=s.type.value,
                            fetch_status=s.fetch_status.value,
                        )
                    )

        return ChatReadModel(
            id=chat.chat_id,
            name=chat.name,
            folder_id=chat.folder_id,
            assistant_id=chat.assistant_id,
            assistant_name=assistant_name,
            model_id=chat.model_id,
            max_context_messages=chat.max_context_messages,
            sources=tuple(sources_list),
            created_at=chat.created_at,
        )

    async def list_standalone_by_owner(
        self, owner_id: UUID
    ) -> Sequence[ChatSummaryReadModel]:
        stmt = (
            select(ChatBase)
            .where(ChatBase.owner_id == owner_id)
            .where(ChatBase.folder_id.is_(None))
            .where(ChatBase.is_active)
            .order_by(ChatBase.created_at.desc())
        )
        rows = await self._executor.execute_scalar_many(stmt)
        return [
            ChatSummaryReadModel(
                id=r.chat_id,
                name=r.name,
                model_id=r.model_id,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def list_messages(
        self,
        chat_id: UUID,
        owner_id: UUID,
        *,
        limit: int = 50,
        before: UUID | None = None,
    ) -> Sequence[MessageReadModel]:
        subq = (
            select(ChatBase.chat_id)
            .where(ChatBase.chat_id == chat_id)
            .where(ChatBase.owner_id == owner_id)
            .where(ChatBase.is_active)
        )
        stmt = (
            select(MessageBase)
            .where(MessageBase.chat_id.in_(subq))
            .order_by(MessageBase.created_at.desc())
            .limit(limit)
            .options(joinedload(MessageBase.attachments))
        )
        if before is not None:
            before_subq = (
                select(MessageBase.created_at)
                .where(MessageBase.message_id == before)
                .scalar_subquery()
            )
            stmt = stmt.where(MessageBase.created_at < before_subq)

        rows = await self._executor.execute_scalar_many(stmt)
        result: list[MessageReadModel] = []
        for r in rows:
            attachments = [
                AttachmentReadModel(
                    name=a.name,
                    content_id=a.content_id,
                    source_id=a.source_id,
                )
                for a in (r.attachments or [])
            ]
            result.append(
                MessageReadModel(
                    id=r.message_id,
                    chat_id=r.chat_id,
                    role=r.role.value,
                    status=r.status.value,
                    content=r.content,
                    model_id=r.model_id,
                    tokens=r.tokens,
                    created_at=r.created_at,
                    edited_at=r.edited_at,
                    attachments=tuple(attachments),
                )
            )
        return result
