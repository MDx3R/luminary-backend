from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.assistant.infrastructure.database.postgres.sqlalchemy.repositories.assistant_repository import (
    AssistantRepository,
)
from tests.unit.assistant.utils import make_assistant


@pytest.mark.asyncio
class TestAssistantRepository:
    @pytest.fixture(autouse=True)
    def setup(
        self, maker, query_executor: QueryExecutor
    ):
        self.maker = maker
        self.repository = AssistantRepository(query_executor)

    async def _add_assistant(self):
        assistant = make_assistant()
        await self.repository.add(assistant)
        return assistant

    async def test_get_by_id_success(self):
        assistant = await self._add_assistant()
        result = await self.repository.get_by_id(assistant.id)
        assert result.id == assistant.id
        assert result.info.name == assistant.info.name
        assert result.is_deleted is False

    async def test_get_by_id_not_found(self):
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(AssistantId(uuid4()))

    async def test_add_and_get(self):
        assistant = make_assistant()
        await self.repository.add(assistant)
        loaded = await self.repository.get_by_id(assistant.id)
        assert loaded.info.name == assistant.info.name
        assert loaded.instructions.prompt == assistant.instructions.prompt

    async def test_save_updates_entity(self):
        assistant = await self._add_assistant()
        assistant.change_name("Updated Name")
        assistant.change_description("Updated Description")
        await self.repository.save(assistant)
        loaded = await self.repository.get_by_id(assistant.id)
        assert loaded.info.name == "Updated Name"
        assert loaded.info.description == "Updated Description"

    async def test_get_by_id_does_not_return_soft_deleted(self):
        assistant = await self._add_assistant()
        assistant.delete()
        await self.repository.save(assistant)
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(assistant.id)
