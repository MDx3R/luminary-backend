from uuid import uuid4

import pytest
from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from tests.unit.chat.utils import make_chat, make_message

from luminary.chat.domain.enums import Author, MessageStatus
from luminary.chat.domain.value_objects.message_id import MessageId
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.chat_repository import (
    ChatRepository,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.repositories.message_repository import (
    MessageRepository,
)


@pytest.mark.asyncio
class TestMessageReader:
    """Integration tests for MessageRepository as IMessageReader."""

    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor):
        self.maker = maker
        self.chat_repository = ChatRepository(query_executor)
        self.message_repository = MessageRepository(query_executor)

    async def _add_chat_and_messages(self, chat_id=None, count: int = 3):
        chat = make_chat(chat_id=chat_id or uuid4())
        await self.chat_repository.add(chat)
        messages = []
        for i in range(count):
            msg = make_message(
                chat_id=chat.id.value,
                content=f"Message {i}",
                role=Author.USER if i % 2 == 0 else Author.ASSISTANT,
            )
            await self.message_repository.add(msg)
            messages.append(msg)
        return chat, messages

    async def test_get_chat_messages_empty(self):
        chat = make_chat()
        await self.chat_repository.add(chat)
        result = await self.message_repository.get_chat_messages(chat.id)
        assert result == []

    async def test_get_chat_messages_returns_in_order(self):
        _, messages = await self._add_chat_and_messages(count=3)
        chat_id = messages[0].chat_id
        result = await self.message_repository.get_chat_messages(chat_id)
        assert len(result) == 3
        assert [m.content for m in result] == ["Message 0", "Message 1", "Message 2"]
        assert [m.id for m in result] == [m.id for m in messages]

    async def test_get_chat_messages_with_limit(self):
        _, messages = await self._add_chat_and_messages(count=5)
        chat_id = messages[0].chat_id
        result = await self.message_repository.get_chat_messages(chat_id, limit=2)
        assert len(result) == 2
        assert result[0].content == "Message 0"
        assert result[1].content == "Message 1"

    async def test_get_chat_messages_only_for_given_chat(self):
        _, messages_a = await self._add_chat_and_messages(count=2)
        _, messages_b = await self._add_chat_and_messages(count=2)
        chat_id_a = messages_a[0].chat_id
        result = await self.message_repository.get_chat_messages(chat_id_a)
        assert len(result) == 2
        assert all(m.chat_id == chat_id_a for m in result)


@pytest.mark.asyncio
class TestMessageRepository:
    """Integration tests for MessageRepository as IMessageRepository."""

    @pytest.fixture(autouse=True)
    def setup(self, maker, query_executor: QueryExecutor):
        self.maker = maker
        self.chat_repository = ChatRepository(query_executor)
        self.repository = MessageRepository(query_executor)

    async def _add_chat_and_message(self):
        chat = make_chat()
        await self.chat_repository.add(chat)
        message = make_message(chat_id=chat.id.value, content="Initial")
        await self.repository.add(message)
        return chat, message

    async def test_get_by_id_success(self):
        _, message = await self._add_chat_and_message()
        result = await self.repository.get_by_id(message.id)
        assert result.id == message.id
        assert result.chat_id == message.chat_id
        assert result.content == message.content
        assert result.role == message.role
        assert result.status == message.status

    async def test_get_by_id_not_found(self):
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(MessageId(uuid4()))

    async def test_add_and_get(self):
        _, message = await self._add_chat_and_message()
        loaded = await self.repository.get_by_id(message.id)
        assert loaded.content == message.content
        assert loaded.model_id == message.model_id

    async def test_save_updates_entity(self):
        _, message = await self._add_chat_and_message()
        message.add_chunk(" appended")
        message.complete(tokens=10)
        await self.repository.save(message)
        loaded = await self.repository.get_by_id(message.id)
        assert loaded.content == "Initial appended"
        assert loaded.status == MessageStatus.COMPLETED
        assert loaded.tokens == 10
