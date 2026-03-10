"""Read repository implementation for Folder: ORM -> read models (cross-BC)."""

from collections.abc import Sequence
from uuid import UUID

from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from sqlalchemy import select
from sqlalchemy.orm import joinedload, with_polymorphic

from luminary.assistant.infrastructure.database.postgres.sqlalchemy.models.assistant_base import (
    AssistantBase,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.chat_base import (
    ChatBase,
)
from luminary.folder.application.dtos.read_models import (
    FolderChatItem,
    FolderEditorItem,
    FolderReadModel,
    FolderSourceItem,
    FolderSummaryReadModel,
)
from luminary.folder.application.interfaces.repositories.folder_read_repository import (
    IFolderReadRepository,
)
from luminary.folder.infrastructure.database.postgres.sqlalchemy.models.folder_base import (
    FolderBase,
)
from luminary.source.infrastructure.database.postgres.sqlalchemy.models.source_base import (
    SourceBase,
)


class FolderReadRepository(IFolderReadRepository):
    def __init__(self, executor: QueryExecutor) -> None:
        self._executor = executor

    async def get_by_id(self, folder_id: UUID, owner_id: UUID) -> FolderReadModel:
        stmt = (
            select(FolderBase)
            .where(FolderBase.folder_id == folder_id)
            .where(FolderBase.owner_id == owner_id)
            .where(FolderBase.is_active)
            .options(
                joinedload(FolderBase.chat_associations),
                joinedload(FolderBase.source_associations),
            )
        )
        folder = await self._executor.execute_scalar_one(stmt)
        if not folder:
            raise NotFoundError(str(folder_id))

        assistant_name: str | None = None
        if folder.assistant_id:
            astmt = (
                select(AssistantBase.name)
                .where(AssistantBase.assistant_id == folder.assistant_id)
                .where(AssistantBase.is_active)
            )
            assistant_name = await self._executor.execute_scalar_one(astmt)

        editor: FolderEditorItem | None = None
        if folder.editor_text is not None and folder.editor_updated_at is not None:
            editor = FolderEditorItem(
                text=folder.editor_text,
                updated_at=folder.editor_updated_at,
            )

        chat_ids = [a.chat_id for a in folder.chat_associations]
        chats_list: list[FolderChatItem] = []
        if chat_ids:
            cstmt = (
                select(ChatBase)
                .where(ChatBase.chat_id.in_(chat_ids))
                .where(ChatBase.is_active)
            )
            chat_rows = await self._executor.execute_scalar_many(cstmt)
            id_to_chat = {r.chat_id: r for r in chat_rows}
            for cid in chat_ids:
                c = id_to_chat.get(cid)
                if c:
                    chats_list.append(
                        FolderChatItem(
                            id=c.chat_id,
                            name=c.name,
                            model_id=c.model_id,
                            created_at=c.created_at,
                        )
                    )

        source_ids = [a.source_id for a in folder.source_associations]
        sources_list: list[FolderSourceItem] = []
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
                        FolderSourceItem(
                            id=s.source_id,
                            title=s.title,
                            type=s.type.value,
                            fetch_status=s.fetch_status.value,
                        )
                    )

        return FolderReadModel(
            id=folder.folder_id,
            name=folder.name,
            description=folder.description,
            assistant_id=folder.assistant_id,
            assistant_name=assistant_name,
            editor=editor,
            chats=tuple(chats_list),
            sources=tuple(sources_list),
            created_at=folder.created_at,
        )

    async def list_by_owner(self, owner_id: UUID) -> Sequence[FolderSummaryReadModel]:
        stmt = (
            select(FolderBase)
            .where(FolderBase.owner_id == owner_id)
            .where(FolderBase.is_active)
            .order_by(FolderBase.created_at.desc())
        )
        rows = await self._executor.execute_scalar_many(stmt)
        return [
            FolderSummaryReadModel(
                id=r.folder_id,
                name=r.name,
                description=r.description,
                created_at=r.created_at,
            )
            for r in rows
        ]
