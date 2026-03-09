from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.chat.utils import make_chat

from luminary.chat.domain.value_objects.chat_id import ChatId
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.chat_repository import (
    ChatRepository,
)
from luminary.source.domain.entity.source import SourceId


@pytest.mark.asyncio
class TestChatRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor):
        self.maker = maker
        self.repository = ChatRepository(query_executor)

    async def _add_chat(self):
        chat = make_chat()
        await self.repository.add(chat)
        return chat

    async def test_get_by_id_success(self):
        chat = await self._add_chat()
        result = await self.repository.get_by_id(chat.id)
        assert result.id == chat.id
        assert result.info.name == chat.info.name
        assert result.is_deleted is False

    async def test_get_by_id_not_found(self):
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(ChatId(uuid4()))

    async def test_add_and_get(self):
        chat = make_chat()
        await self.repository.add(chat)
        loaded = await self.repository.get_by_id(chat.id)
        assert loaded.info.name == chat.info.name

    async def test_save_with_sources(self):
        chat = await self._add_chat()

        chat.add_source(SourceId(uuid4()))
        await self.repository.save(chat)
        loaded = await self.repository.get_by_id(chat.id)
        assert len(loaded.sources) == 1

    async def test_get_by_id_does_not_return_soft_deleted(self):
        chat = await self._add_chat()
        chat.delete()
        await self.repository.save(chat)
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(chat.id)
