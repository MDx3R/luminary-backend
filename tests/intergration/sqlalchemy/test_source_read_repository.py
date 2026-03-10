"""Integration tests for SourceReadRepository."""

from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.source.utils import make_file_source, make_link_source, make_page_source

from luminary.source.infrastructure.database.postgres.sqlalchemy.repositories.source_read_repository import (
    SourceReadRepository,
)
from luminary.source.infrastructure.database.postgres.sqlalchemy.repositories.source_repository import (
    SourceRepository,
)


@pytest.mark.asyncio
class TestSourceReadRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor) -> None:
        self.write_repo = SourceRepository(query_executor)
        self.read_repo = SourceReadRepository(query_executor)

    async def _add_file_source(self, owner_id=None):
        owner_id = owner_id or uuid4()
        source = make_file_source(owner_id=owner_id)
        await self.write_repo.add(source)
        return source

    async def _add_link_source(self, owner_id=None):
        owner_id = owner_id or uuid4()
        source = make_link_source(owner_id=owner_id, url="https://link.test")
        await self.write_repo.add(source)
        return source

    async def _add_page_source(self, owner_id=None):
        owner_id = owner_id or uuid4()
        source = make_page_source(owner_id=owner_id, editable=False)
        await self.write_repo.add(source)
        return source

    # --- get_by_id ---

    async def test_get_by_id_file_source_returns_read_model(self) -> None:
        source = await self._add_file_source()
        owner_id = source.owner_id.value

        result = await self.read_repo.get_by_id(source.id.value, owner_id)

        assert result.id == source.id.value
        assert result.title == source.title.value
        assert result.type == "file"
        assert result.file_id == source.file_id.value
        assert result.url is None
        assert result.editable is None

    async def test_get_by_id_link_source_returns_read_model(self) -> None:
        source = await self._add_link_source()
        owner_id = source.owner_id.value

        result = await self.read_repo.get_by_id(source.id.value, owner_id)

        assert result.id == source.id.value
        assert result.title == source.title.value
        assert result.type == "link"
        assert result.url == "https://link.test"
        assert result.file_id is None
        assert result.editable is None

    async def test_get_by_id_page_source_returns_read_model(self) -> None:
        source = await self._add_page_source()
        owner_id = source.owner_id.value

        result = await self.read_repo.get_by_id(source.id.value, owner_id)

        assert result.id == source.id.value
        assert result.type == "page"
        assert result.editable is False
        assert result.url is None
        assert result.file_id is None

    async def test_get_by_id_not_found_raises(self) -> None:
        owner_id = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(uuid4(), owner_id)

    async def test_get_by_id_wrong_owner_raises(self) -> None:
        source = await self._add_file_source()
        other_owner = uuid4()
        assert other_owner != source.owner_id.value

        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(source.id.value, other_owner)

    async def test_get_by_id_soft_deleted_raises(self) -> None:
        source = await self._add_file_source()
        source.is_deleted = True
        await self.write_repo.save(source)

        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(source.id.value, source.owner_id.value)

    # --- list_by_owner ---

    async def test_list_by_owner_empty(self) -> None:
        owner_id = uuid4()
        result = await self.read_repo.list_by_owner(owner_id)
        assert list(result) == []

    async def test_list_by_owner_returns_all_ordered_by_created_at_desc(
        self,
    ) -> None:
        owner_id = uuid4()
        s1 = make_file_source(owner_id=owner_id, title="First")
        s2 = make_link_source(owner_id=owner_id, title="Second")
        s3 = make_page_source(owner_id=owner_id, title="Third")
        await self.write_repo.add(s1)
        await self.write_repo.add(s2)
        await self.write_repo.add(s3)

        result = await self.read_repo.list_by_owner(owner_id)

        assert len(result) == 3  # noqa: PLR2004
        titles = [r.title for r in result]
        assert "First" in titles
        assert "Second" in titles
        assert "Third" in titles
        assert result[0].created_at >= result[1].created_at >= result[2].created_at

    async def test_list_by_owner_excludes_other_owner(self) -> None:
        owner_a = uuid4()
        owner_b = uuid4()
        await self._add_file_source(owner_id=owner_a)

        result = await self.read_repo.list_by_owner(owner_b)
        assert list(result) == []

    async def test_list_by_owner_excludes_soft_deleted(self) -> None:
        owner_id = uuid4()
        source = make_file_source(owner_id=owner_id)
        await self.write_repo.add(source)
        source.is_deleted = True
        await self.write_repo.save(source)

        result = await self.read_repo.list_by_owner(owner_id)
        assert list(result) == []
