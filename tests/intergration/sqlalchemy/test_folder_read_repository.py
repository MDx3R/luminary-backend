"""Integration tests for FolderReadRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.domain.value_objects.datetime import DateTime
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.assistant.utils import make_assistant
from tests.unit.chat.utils import make_chat
from tests.unit.folder.utils import make_folder
from tests.unit.source.utils import make_file_source, make_link_source, make_page_source

from luminary.assistant.infrastructure.database.postgres.sqlalchemy.repositories.assistant_repository import (
    AssistantRepository,
)
from luminary.chat.domain.value_objects.chat_id import ChatId
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.chat_repository import (
    ChatRepository,
)
from luminary.folder.infrastructure.database.postgres.sqlalchemy.repositories.folder_read_repository import (
    FolderReadRepository,
)
from luminary.folder.infrastructure.database.postgres.sqlalchemy.repositories.folder_repository import (
    FolderRepository,
)
from luminary.source.domain.entity.file_source import FileSource
from luminary.source.domain.entity.link_source import LinkSource
from luminary.source.domain.entity.page_source import PageSource
from luminary.source.domain.entity.source import Source, SourceId
from luminary.source.infrastructure.database.postgres.sqlalchemy.repositories.source_repository import (
    SourceRepository,
)


@pytest.mark.asyncio
class TestFolderReadRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor) -> None:
        self.folder_repo = FolderRepository(query_executor)
        self.source_repo = SourceRepository(query_executor)
        self.assistant_repo = AssistantRepository(query_executor)
        self.chat_repo = ChatRepository(query_executor)
        self.read_repo = FolderReadRepository(query_executor)

    async def _add_folder(self, owner_id=None):
        owner_id = owner_id or uuid4()
        folder = make_folder(owner_id=owner_id)
        await self.folder_repo.add(folder)
        return folder

    # --- get_by_id ---

    async def test_get_by_id_returns_read_model_minimal(self) -> None:
        folder = await self._add_folder()
        owner_id = folder.owner_id.value

        result = await self.read_repo.get_by_id(folder.id.value, owner_id)

        assert result.id == folder.id.value
        assert result.name == folder.info.name
        assert result.description == folder.info.description
        assert result.assistant_id is None
        assert result.assistant_name is None
        assert result.editor is None
        assert result.chats == []
        assert result.sources == []

    async def test_get_by_id_with_editor_returns_editor_item(self) -> None:
        folder = await self._add_folder()
        folder.update_editor_content(
            "Editor text",
            DateTime(datetime.now(UTC)),
        )
        await self.folder_repo.save(folder)
        owner_id = folder.owner_id.value

        result = await self.read_repo.get_by_id(folder.id.value, owner_id)

        assert result.editor is not None
        assert result.editor.text == "Editor text"

    @pytest.mark.parametrize(
        "source", [make_file_source(), make_page_source(), make_link_source()]
    )
    async def test_get_by_id_with_chats_and_sources_returns_items(
        self, source: Source
    ) -> None:
        owner_id = source.owner_id.value
        await self.source_repo.add(source)
        chat = make_chat(user_id=owner_id)
        await self.chat_repo.add(chat)
        folder = make_folder(owner_id=owner_id)
        folder.add_chat(ChatId(chat.id.value))
        folder.add_source(SourceId(source.id.value))
        await self.folder_repo.add(folder)

        result = await self.read_repo.get_by_id(folder.id.value, owner_id)

        assert len(result.chats) == 1
        assert result.chats[0].id == chat.id.value
        assert result.chats[0].name == chat.info.name
        assert len(result.sources) == 1
        assert result.sources[0].id == source.id.value
        assert result.sources[0].title == source.title.value
        assert result.sources[0].type == source.type.value

        match source:
            case FileSource():
                assert result.sources[0].file_id == source.file_id.value
            case PageSource():
                assert result.sources[0].editable == source.editable
            case LinkSource():
                assert result.sources[0].url == source.url.value

    async def test_get_by_id_with_assistant_returns_assistant_name(
        self,
    ) -> None:
        owner_id = uuid4()
        assistant = make_assistant(user_id=owner_id, name="Folder Assistant")
        await self.assistant_repo.add(assistant)
        folder = make_folder(owner_id=owner_id, assistant_id=assistant.id.value)
        await self.folder_repo.add(folder)

        result = await self.read_repo.get_by_id(folder.id.value, owner_id)

        assert result.assistant_id == assistant.id.value
        assert result.assistant_name == "Folder Assistant"

    async def test_get_by_id_not_found_raises(self) -> None:
        owner_id = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(uuid4(), owner_id)

    async def test_get_by_id_wrong_owner_raises(self) -> None:
        folder = await self._add_folder()
        other_owner = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(folder.id.value, other_owner)

    async def test_get_by_id_soft_deleted_raises(self) -> None:
        folder = await self._add_folder()
        folder.delete()
        await self.folder_repo.save(folder)
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(folder.id.value, folder.owner_id.value)

    # --- list_by_owner ---

    async def test_list_by_owner_empty(self) -> None:
        result = await self.read_repo.list_by_owner(uuid4())
        assert list(result) == []

    async def test_list_by_owner_returns_summaries_ordered_by_created_at_desc(
        self,
    ) -> None:
        owner_id = uuid4()
        f1 = make_folder(owner_id=owner_id)
        f2 = make_folder(owner_id=owner_id)
        await self.folder_repo.add(f1)
        await self.folder_repo.add(f2)

        result = await self.read_repo.list_by_owner(owner_id)

        assert len(result) == 2  # noqa: PLR2004
        names = {r.name for r in result}
        assert names == {f1.info.name, f2.info.name}
        assert result[0].created_at >= result[1].created_at

    async def test_list_by_owner_excludes_other_owner(self) -> None:
        owner_a = uuid4()
        await self._add_folder(owner_id=owner_a)

        result = await self.read_repo.list_by_owner(uuid4())
        assert list(result) == []

    async def test_list_by_owner_excludes_soft_deleted(self) -> None:
        owner_id = uuid4()
        folder = make_folder(owner_id=owner_id)
        await self.folder_repo.add(folder)
        folder.delete()
        await self.folder_repo.save(folder)

        result = await self.read_repo.list_by_owner(owner_id)
        assert list(result) == []
