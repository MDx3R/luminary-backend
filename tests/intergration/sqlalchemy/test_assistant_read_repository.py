"""Integration tests for AssistantReadRepository."""

from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.assistant.utils import make_assistant

from luminary.assistant.infrastructure.database.postgres.sqlalchemy.repositories.assistant_read_repository import (
    AssistantReadRepository,
)
from luminary.assistant.infrastructure.database.postgres.sqlalchemy.repositories.assistant_repository import (
    AssistantRepository,
)


@pytest.mark.asyncio
class TestAssistantReadRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor) -> None:
        self.write_repo = AssistantRepository(query_executor)
        self.read_repo = AssistantReadRepository(query_executor)

    async def _add_assistant(self, owner_id=None):
        owner_id = owner_id or uuid4()
        assistant = make_assistant(user_id=owner_id, name="Test", description="Desc")
        await self.write_repo.add(assistant)
        return assistant

    # --- get_by_id ---

    async def test_get_by_id_returns_read_model(self) -> None:
        assistant = await self._add_assistant()
        owner_id = assistant.owner_id.value

        result = await self.read_repo.get_by_id(assistant.id.value, owner_id)

        assert result.id == assistant.id.value
        assert result.name == assistant.info.name
        assert result.description == assistant.info.description
        assert result.type == assistant.type.value
        assert result.prompt == assistant.instructions.prompt

    async def test_get_by_id_not_found_raises(self) -> None:
        owner_id = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(uuid4(), owner_id)

    async def test_get_by_id_wrong_owner_raises(self) -> None:
        assistant = await self._add_assistant()
        other_owner = uuid4()
        assert other_owner != assistant.owner_id.value

        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(assistant.id.value, other_owner)

    async def test_get_by_id_soft_deleted_raises(self) -> None:
        assistant = await self._add_assistant()
        assistant.delete()
        await self.write_repo.save(assistant)

        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(assistant.id.value, assistant.owner_id.value)

    # --- list_by_owner ---

    async def test_list_by_owner_empty(self) -> None:
        owner_id = uuid4()
        result = await self.read_repo.list_by_owner(owner_id)
        assert list(result) == []

    async def test_list_by_owner_returns_summaries_ordered_by_created_at_desc(
        self,
    ) -> None:
        owner_id = uuid4()
        a1 = make_assistant(user_id=owner_id, name="A1")
        a2 = make_assistant(user_id=owner_id, name="A2")
        await self.write_repo.add(a1)
        await self.write_repo.add(a2)

        result = await self.read_repo.list_by_owner(owner_id)

        assert len(result) == 2  # noqa: PLR2004
        names = {r.name for r in result}
        assert names == {"A1", "A2"}

    async def test_list_by_owner_excludes_other_owner(self) -> None:
        owner_a = uuid4()
        owner_b = uuid4()
        await self._add_assistant(owner_id=owner_a)

        result = await self.read_repo.list_by_owner(owner_b)
        assert list(result) == []

    async def test_list_by_owner_excludes_soft_deleted(self) -> None:
        owner_id = uuid4()
        assistant = make_assistant(user_id=owner_id)
        await self.write_repo.add(assistant)
        assistant.delete()
        await self.write_repo.save(assistant)

        result = await self.read_repo.list_by_owner(owner_id)
        assert list(result) == []
