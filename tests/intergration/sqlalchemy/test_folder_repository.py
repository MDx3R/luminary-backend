from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.folder.utils import make_folder

from luminary.chat.domain.value_objects.chat_id import ChatId
from luminary.folder.domain.value_objects.folder_id import FolderId
from luminary.folder.infrastructure.database.postgres.sqlalchemy.repositories.folder_repository import (
    FolderRepository,
)
from luminary.source.domain.entity.source import SourceId


@pytest.mark.asyncio
class TestFolderRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor):
        self.maker = maker
        self.repository = FolderRepository(query_executor)

    async def _add_folder(self):
        folder = make_folder()
        await self.repository.add(folder)
        return folder

    async def test_get_by_id_success(self):
        folder = await self._add_folder()
        result = await self.repository.get_by_id(folder.id)
        assert result.id == folder.id
        assert result.info.name == folder.info.name
        assert result.is_deleted is False

    async def test_get_by_id_not_found(self):
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(FolderId(uuid4()))

    async def test_add_and_get(self):
        folder = make_folder()
        await self.repository.add(folder)
        loaded = await self.repository.get_by_id(folder.id)
        assert loaded.info.name == folder.info.name

    async def test_save_with_chats_and_sources(self):
        folder = await self._add_folder()

        folder.add_chat(ChatId(uuid4()))
        folder.add_source(SourceId(uuid4()))
        await self.repository.save(folder)
        loaded = await self.repository.get_by_id(folder.id)
        assert len(loaded.chats) == 1
        assert len(loaded.sources) == 1

    async def test_get_by_id_does_not_return_soft_deleted(self):
        folder = await self._add_folder()
        folder.delete()
        await self.repository.save(folder)
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(folder.id)
