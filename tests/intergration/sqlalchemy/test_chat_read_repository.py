"""Integration tests for ChatReadRepository."""

from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.assistant.utils import make_assistant
from tests.unit.chat.utils import make_chat, make_message
from tests.unit.source.utils import make_file_source, make_link_source, make_page_source

from luminary.assistant.infrastructure.database.postgres.sqlalchemy.repositories.assistant_repository import (
    AssistantRepository,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.attachment_base import (
    AttachmentBase,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.chat_read_repository import (
    ChatReadRepository,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.chat_repository import (
    ChatRepository,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.message_repository import (
    MessageRepository,
)
from luminary.source.domain.entity.file_source import FileSource
from luminary.source.domain.entity.link_source import LinkSource
from luminary.source.domain.entity.page_source import PageSource
from luminary.source.domain.entity.source import Source, SourceId
from luminary.source.infrastructure.database.postgres.sqlalchemy.repositories.source_repository import (
    SourceRepository,
)


@pytest.mark.asyncio
class TestChatReadRepository:
    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor) -> None:
        self.query_executor = query_executor
        self.chat_repo = ChatRepository(query_executor)
        self.message_repo = MessageRepository(query_executor)
        self.source_repo = SourceRepository(query_executor)
        self.assistant_repo = AssistantRepository(query_executor)
        self.read_repo = ChatReadRepository(query_executor)

    async def _add_chat(self, owner_id=None, folder_id=None, assistant_id=None):
        owner_id = owner_id or uuid4()
        chat = make_chat(
            user_id=owner_id, folder_id=folder_id, assistant_id=assistant_id
        )
        await self.chat_repo.add(chat)
        return chat

    async def _add_message(self, chat_id, content="Msg"):
        message = make_message(chat_id=chat_id, content=content)
        await self.message_repo.add(message)
        return message

    # --- get_by_id ---

    async def test_get_by_id_returns_read_model_no_sources_no_assistant(
        self,
    ) -> None:
        chat = await self._add_chat()
        owner_id = chat.owner_id.value

        result = await self.read_repo.get_by_id(chat.id.value, owner_id)

        assert result.id == chat.id.value
        assert result.name == chat.info.name
        assert result.folder_id is None
        assert result.assistant_id is None
        assert result.assistant_name is None
        assert result.sources == []

    @pytest.mark.parametrize(
        "source", [make_file_source(), make_page_source(), make_link_source()]
    )
    async def test_get_by_id_with_sources_returns_source_items(
        self, source: Source
    ) -> None:
        owner_id = source.owner_id.value
        await self.source_repo.add(source)
        chat = make_chat(user_id=owner_id)
        chat.add_source(SourceId(source.id.value))
        await self.chat_repo.add(chat)

        result = await self.read_repo.get_by_id(chat.id.value, owner_id)

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

    async def test_get_by_id_with_assistant_returns_assistant_name(self) -> None:
        owner_id = uuid4()
        assistant = make_assistant(user_id=owner_id, name="My Assistant")
        await self.assistant_repo.add(assistant)
        chat = make_chat(user_id=owner_id, assistant_id=assistant.id.value)
        await self.chat_repo.add(chat)

        result = await self.read_repo.get_by_id(chat.id.value, owner_id)

        assert result.assistant_id == assistant.id.value
        assert result.assistant_name == "My Assistant"

    async def test_get_by_id_not_found_raises(self) -> None:
        owner_id = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(uuid4(), owner_id)

    async def test_get_by_id_wrong_owner_raises(self) -> None:
        chat = await self._add_chat()
        other_owner = uuid4()
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(chat.id.value, other_owner)

    async def test_get_by_id_soft_deleted_raises(self) -> None:
        chat = await self._add_chat()
        chat.delete()
        await self.chat_repo.save(chat)
        with pytest.raises(NotFoundError):
            await self.read_repo.get_by_id(chat.id.value, chat.owner_id.value)

    # --- list_standalone_by_owner ---

    async def test_list_standalone_by_owner_empty(self) -> None:
        result = await self.read_repo.list_standalone_by_owner(uuid4())
        assert list(result) == []

    async def test_list_standalone_by_owner_returns_only_standalone_chats(
        self,
    ) -> None:
        owner_id = uuid4()
        await self._add_chat(owner_id=owner_id, folder_id=None)
        folder_id = uuid4()
        await self._add_chat(owner_id=owner_id, folder_id=folder_id)

        result = await self.read_repo.list_standalone_by_owner(owner_id)

        assert len(result) == 1

    async def test_list_standalone_by_owner_excludes_other_owner(self) -> None:
        owner_a = uuid4()
        await self._add_chat(owner_id=owner_a)

        result = await self.read_repo.list_standalone_by_owner(uuid4())
        assert list(result) == []

    async def test_list_standalone_by_owner_excludes_soft_deleted(self) -> None:
        owner_id = uuid4()
        chat = make_chat(user_id=owner_id)
        await self.chat_repo.add(chat)
        chat.delete()
        await self.chat_repo.save(chat)

        result = await self.read_repo.list_standalone_by_owner(owner_id)
        assert list(result) == []

    # --- list_messages ---

    async def test_list_messages_empty(self) -> None:
        chat = await self._add_chat()
        result = await self.read_repo.list_messages(chat.id.value, chat.owner_id.value)
        assert list(result) == []

    async def test_list_messages_returns_ordered_by_created_at_desc(self) -> None:
        chat = await self._add_chat()
        await self._add_message(chat.id.value, "First")
        await self._add_message(chat.id.value, "Second")
        await self._add_message(chat.id.value, "Third")

        result = await self.read_repo.list_messages(
            chat.id.value, chat.owner_id.value, limit=10
        )

        assert len(result) == 3  # noqa: PLR2004
        assert result[0].content == "Third"
        assert result[1].content == "Second"
        assert result[2].content == "First"

    async def test_list_messages_respects_limit(self) -> None:
        chat = await self._add_chat()
        await self._add_message(chat.id.value, "A")
        await self._add_message(chat.id.value, "B")
        await self._add_message(chat.id.value, "C")

        result = await self.read_repo.list_messages(
            chat.id.value, chat.owner_id.value, limit=2
        )

        assert len(result) == 2  # noqa: PLR2004

    async def test_list_messages_before_cursor(self) -> None:
        chat = await self._add_chat()
        await self._add_message(chat.id.value, "First")
        await self._add_message(chat.id.value, "Second")
        m3 = await self._add_message(chat.id.value, "Third")

        result = await self.read_repo.list_messages(
            chat.id.value,
            chat.owner_id.value,
            limit=10,
            before=m3.id.value,
        )

        assert len(result) == 2  # noqa: PLR2004
        contents = [r.content for r in result]
        assert "Third" not in contents
        assert "Second" in contents
        assert "First" in contents

    async def test_list_messages_wrong_owner_returns_empty(self) -> None:
        chat = await self._add_chat()
        await self._add_message(chat.id.value, "Hi")

        result = await self.read_repo.list_messages(chat.id.value, uuid4())
        assert list(result) == []

    async def test_list_messages_with_attachments(self) -> None:
        chat = await self._add_chat()
        message = await self._add_message(chat.id.value, "With attachment")
        att = AttachmentBase(
            message_id=message.id.value,
            name="file.pdf",
            content_id=uuid4(),
            source_id=None,
        )
        await self.query_executor.add(att)

        result = await self.read_repo.list_messages(chat.id.value, chat.owner_id.value)

        assert len(result) == 1
        assert len(result[0].attachments) == 1
        assert result[0].attachments[0].name == "file.pdf"
