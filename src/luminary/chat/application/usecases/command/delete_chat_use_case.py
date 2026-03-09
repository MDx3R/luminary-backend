from common.domain.value_objects.id import UserId

from luminary.chat.application.interfaces.policies.chat_access_policy import (
    IChatAccessPolicy,
)
from luminary.chat.application.interfaces.repositories.chat_repository import (
    IChatRepository,
)
from luminary.chat.application.interfaces.usecases.command.delete_chat_use_case import (
    DeleteChatCommand,
    IDeleteChatUseCase,
)
from luminary.chat.domain.value_objects.chat_id import ChatId


class DeleteChatUseCase(IDeleteChatUseCase):
    def __init__(
        self,
        repository: IChatRepository,
        access_policy: IChatAccessPolicy,
    ) -> None:
        self.repository = repository
        self.access_policy = access_policy

    async def execute(self, command: DeleteChatCommand) -> None:
        chat = await self.repository.get_by_id(ChatId(command.chat_id))
        self.access_policy.assert_is_allowed(UserId(command.user_id), chat)

        chat.delete()
        await self.repository.save(chat)
