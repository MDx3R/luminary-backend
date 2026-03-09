from common.application.interfaces.handlers.handler import IEventHandler

from luminary.chat.application.interfaces.repositories.chat_repository import (
    IChatRepository,
)
from luminary.source.domain.entity.source import SourceId
from luminary.source.domain.events.events import SourceDeletedEvent


class ChatSourceDeletedHandler(IEventHandler[SourceDeletedEvent]):
    """Clears source reference in chats when an source is soft-deleted."""

    def __init__(self, chat_repository: IChatRepository) -> None:
        self.chat_repository = chat_repository

    async def handle(self, event: SourceDeletedEvent) -> None:
        await self.chat_repository.clear_source_reference(SourceId(event.source_id))
