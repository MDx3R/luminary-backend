from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.folder.application.interfaces.repositories.folder_repository import (
    IFolderRepository,
)
from luminary.folder.domain.entity.folder import Folder
from luminary.folder.domain.value_objects.folder_id import FolderId
from luminary.folder.infrastructure.database.postgres.sqlalchemy.mappers.folder_mapper import (
    FolderMapper,
)
from luminary.folder.infrastructure.database.postgres.sqlalchemy.models.folder_base import (
    FolderBase,
)


class FolderRepository(IFolderRepository):
    def __init__(self, executor: QueryExecutor) -> None:
        self.executor = executor

    async def get_by_id(self, id: FolderId) -> Folder:
        stmt = (
            select(FolderBase)
            .where(FolderBase.folder_id == id.value)
            .where(FolderBase.is_active)
            .options(
                joinedload(FolderBase.chat_associations),
                joinedload(FolderBase.source_associations),
            )
        )
        base = await self.executor.execute_scalar_one(stmt)
        if base is None:
            raise NotFoundError(id)

        return FolderMapper.to_domain(base)

    async def add(self, entity: Folder) -> None:
        base = FolderMapper.to_persistence(entity)
        await self.executor.add(base)

    async def save(self, entity: Folder) -> None:
        base = FolderMapper.to_persistence(entity)
        await self.executor.save(base)

    async def clear_assistant_reference(self, assistant_id: AssistantId) -> None:
        stmt = (
            update(FolderBase)
            .where(FolderBase.assistant_id == assistant_id.value)
            .values(assistant_id=None)
        )
        await self.executor.execute(stmt)
