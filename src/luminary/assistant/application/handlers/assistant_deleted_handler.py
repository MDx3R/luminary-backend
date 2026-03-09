from common.application.interfaces.handlers.handler import IEventHandler

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.assistant.domain.events.events import AssistantDeletedEvent
from luminary.chat.application.interfaces.repositories.chat_repository import (
    IChatRepository,
)
from luminary.folder.application.interfaces.repositories.folder_repository import (
    IFolderRepository,
)


class AssistantDeletedHandler(IEventHandler[AssistantDeletedEvent]):
    """Clears assistant_id reference in folders and chats when an assistant is soft-deleted."""

    def __init__(
        self,
        chat_repository: IChatRepository,
        folder_repository: IFolderRepository,
    ) -> None:
        self.chat_repository = chat_repository
        self.folder_repository = folder_repository

    async def handle(self, event: AssistantDeletedEvent) -> None:
        assistant_id = AssistantId(event.assistant_id)
        await self.chat_repository.clear_assistant_reference(assistant_id)
        await self.folder_repository.clear_assistant_reference(assistant_id)
