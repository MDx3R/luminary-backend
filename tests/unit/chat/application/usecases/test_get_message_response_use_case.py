from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from common.application.exceptions import AccessPolicyError, NotFoundError
from common.application.interfaces.transactions.unit_of_work import IUnitOfWork
from tests.unit.chat.utils import make_chat, make_chat_settings, make_message

from luminary.chat.application.interfaces.policies.chat_access_policy import (
    IChatAccessPolicy,
)
from luminary.chat.application.interfaces.repositories.chat_repository import (
    IChatRepository,
)
from luminary.chat.application.interfaces.repositories.message_reader import (
    IMessageReader,
)
from luminary.chat.application.interfaces.repositories.message_repository import (
    IMessageRepository,
)
from luminary.chat.application.interfaces.usecases.command.get_message_response_use_case import (
    GetMessageResponseCommand,
    StreamState,
)
from luminary.chat.application.usecases.command.get_message_response_use_case import (
    GetStreamingMessageResponseUseCase,
)
from luminary.chat.domain.enums import Author, MessageStatus
from luminary.chat.domain.interfaces.message_factory import (
    IMessageFactory,
)
from luminary.model.application.interfaces.services.engine import (
    EngineStreamingResponse,
    IInferenceEngine,
)


async def _mock_stream(*chunks: str):
    for c in chunks:
        yield EngineStreamingResponse(content=c)


@pytest.mark.asyncio
class TestGetStreamingMessageResponseUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.user_id = uuid4()
        self.chat_id = uuid4()
        self.message_id = uuid4()

        self.chat = make_chat(
            chat_id=self.chat_id,
            user_id=self.user_id,
            settings=make_chat_settings(max_context_messages=5),
        )
        self.user_message = make_message(
            message_id=self.message_id,
            chat_id=self.chat_id,
            role=Author.USER,
            content="Hello",
        )
        self.assistant_message = make_message(
            chat_id=self.chat_id,
            role=Author.ASSISTANT,
            status=MessageStatus.PENDING,
            content="",
        )

        self.chat_repository: AsyncMock = AsyncMock(
            spec=IChatRepository,
            get_by_id=AsyncMock(return_value=self.chat),
        )
        self.message_repository: AsyncMock = AsyncMock(
            spec=IMessageRepository,
            get_by_id=AsyncMock(return_value=self.user_message),
        )
        self.message_reader: AsyncMock = AsyncMock(
            spec=IMessageReader,
            get_chat_messages=AsyncMock(return_value=[self.user_message]),
        )
        self.message_factory: Mock = Mock(spec=IMessageFactory)
        self.message_factory.create.return_value = self.assistant_message
        self.assistant_repository: AsyncMock = AsyncMock()
        self.chat_access_policy: Mock = Mock(spec=IChatAccessPolicy)
        self.inference_engine: Mock = Mock(spec=IInferenceEngine)
        self.inference_engine.send.return_value = _mock_stream("Hi", " there")

        self.uow: Mock = AsyncMock(spec=IUnitOfWork)

        self.command = GetMessageResponseCommand(
            user_id=self.user_id,
            chat_id=self.chat_id,
            message_id=self.message_id,
        )

        self.use_case = GetStreamingMessageResponseUseCase(
            uow=self.uow,
            message_factory=self.message_factory,
            inference_engine=self.inference_engine,
            chat_repository=self.chat_repository,
            assistant_repository=self.assistant_repository,
            message_reader=self.message_reader,
            message_repository=self.message_repository,
            chat_access_policy=self.chat_access_policy,
        )

    async def test_creates_assistant_message_and_streams_chunks(self) -> None:
        chunks = [c async for c in self.use_case.execute(self.command)]

        self.message_repository.add.assert_awaited_once()
        assert self.message_repository.save.await_count >= 1
        assert chunks[0].state == StreamState.START
        content_chunks = [c for c in chunks if c.state == StreamState.DELTA]
        assert content_chunks[0].content == "Hi"
        assert content_chunks[1].content == " there"
        assert chunks[-1].state == StreamState.END
        assert chunks[-1].message_id == self.assistant_message.id.value

    async def test_calls_access_policy_with_user_and_chat(self) -> None:
        async for _ in self.use_case.execute(self.command):
            pass

        self.chat_access_policy.assert_is_allowed.assert_called_once()

    async def test_raises_not_found_when_message_not_in_chat(self) -> None:
        other_message_id = uuid4()
        self.message_reader.get_chat_messages.return_value = [
            make_message(
                message_id=other_message_id,
                chat_id=self.chat_id,
                role=Author.USER,
            )
        ]

        with pytest.raises(NotFoundError):
            async for _ in self.use_case.execute(self.command):
                pass

    async def test_raises_access_policy_error_when_access_denied(self) -> None:
        self.chat_access_policy.assert_is_allowed.side_effect = AccessPolicyError(
            self.chat.id, "Access denied"
        )

        with pytest.raises(AccessPolicyError):
            async for _ in self.use_case.execute(self.command):
                pass
