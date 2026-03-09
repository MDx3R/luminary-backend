from typing import Annotated
from uuid import UUID

from common.presentation.http.dto.response import IDResponse
from common.presentation.http.fastapi.auth import get_descriptor
from common.presentation.http.fastapi.cbv import cbv
from fastapi import APIRouter, Depends, status

from luminary.chat.application.interfaces.usecases.command.add_source_to_chat_use_case import (
    AddSourceToChatCommand,
    IAddSourceToChatUseCase,
)
from luminary.chat.application.interfaces.usecases.command.change_chat_assistant_use_case import (
    ChangeChatAssistantCommand,
    IChangeChatAssistantUseCase,
)
from luminary.chat.application.interfaces.usecases.command.create_chat_use_case import (
    CreateChatCommand,
    ICreateChatUseCase,
)
from luminary.chat.application.interfaces.usecases.command.delete_chat_use_case import (
    DeleteChatCommand,
    IDeleteChatUseCase,
)
from luminary.chat.application.interfaces.usecases.command.remove_chat_assistant_use_case import (
    IRemoveChatAssistantUseCase,
    RemoveChatAssistantCommand,
)
from luminary.chat.application.interfaces.usecases.command.remove_source_from_chat_use_case import (
    IRemoveSourceFromChatUseCase,
    RemoveSourceFromChatCommand,
)
from luminary.chat.application.interfaces.usecases.command.update_chat_name_use_case import (
    IUpdateChatNameUseCase,
    UpdateChatNameCommand,
)
from luminary.chat.application.interfaces.usecases.command.update_chat_settings_use_case import (
    IUpdateChatSettingsUseCase,
    UpdateChatSettingsCommand,
)
from luminary.chat.presentation.http.dto.request import (
    AddSourceToChatRequest,
    ChangeChatAssistantRequest,
    CreateChatRequest,
    UpdateChatNameRequest,
    UpdateChatSettingsRequest,
)


command_router = APIRouter()


@cbv(command_router)
class ChatCommandController:
    create_chat_use_case: ICreateChatUseCase = Depends()
    update_chat_name_use_case: IUpdateChatNameUseCase = Depends()
    update_chat_settings_use_case: IUpdateChatSettingsUseCase = Depends()
    change_chat_assistant_use_case: IChangeChatAssistantUseCase = Depends()
    remove_chat_assistant_use_case: IRemoveChatAssistantUseCase = Depends()
    add_source_to_chat_use_case: IAddSourceToChatUseCase = Depends()
    remove_source_from_chat_use_case: IRemoveSourceFromChatUseCase = Depends()
    delete_chat_use_case: IDeleteChatUseCase = Depends()

    @command_router.post("", status_code=status.HTTP_201_CREATED)
    async def create(
        self,
        request: Annotated[CreateChatRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> IDResponse:
        chat_id = await self.create_chat_use_case.execute(
            CreateChatCommand(
                user_id=descriptor,
                folder_id=None,
                name=request.name,
                assistant_id=request.assistant_id,
                model_id=request.model_id,
                max_context_messages=request.max_context_messages,
            )
        )
        return IDResponse(id=chat_id)

    @command_router.put(
        "/{chat_id:uuid}/name",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def update_name(
        self,
        chat_id: UUID,
        request: Annotated[UpdateChatNameRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.update_chat_name_use_case.execute(
            UpdateChatNameCommand(
                user_id=descriptor, chat_id=chat_id, name=request.name
            )
        )

    @command_router.put(
        "/{chat_id:uuid}/settings",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def update_settings(
        self,
        chat_id: UUID,
        request: Annotated[UpdateChatSettingsRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.update_chat_settings_use_case.execute(
            UpdateChatSettingsCommand(
                user_id=descriptor,
                chat_id=chat_id,
                model_id=request.model_id,
                max_context_messages=request.max_context_messages,
            )
        )

    @command_router.put(
        "/{chat_id:uuid}/assistant",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def change_assistant(
        self,
        chat_id: UUID,
        request: Annotated[ChangeChatAssistantRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.change_chat_assistant_use_case.execute(
            ChangeChatAssistantCommand(
                user_id=descriptor,
                chat_id=chat_id,
                assistant_id=request.assistant_id,
            )
        )

    @command_router.delete(
        "/{chat_id:uuid}/assistant",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def remove_assistant(
        self,
        chat_id: UUID,
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.remove_chat_assistant_use_case.execute(
            RemoveChatAssistantCommand(user_id=descriptor, chat_id=chat_id)
        )

    @command_router.post(
        "/{chat_id:uuid}/sources",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def add_source(
        self,
        chat_id: UUID,
        request: Annotated[AddSourceToChatRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.add_source_to_chat_use_case.execute(
            AddSourceToChatCommand(
                user_id=descriptor,
                chat_id=chat_id,
                source_id=request.source_id,
            )
        )

    @command_router.delete(
        "/{chat_id:uuid}/sources/{source_id:uuid}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def remove_source(
        self,
        chat_id: UUID,
        source_id: UUID,
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.remove_source_from_chat_use_case.execute(
            RemoveSourceFromChatCommand(
                user_id=descriptor,
                chat_id=chat_id,
                source_id=source_id,
            )
        )

    @command_router.delete(
        "/{chat_id:uuid}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete(
        self,
        chat_id: UUID,
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.delete_chat_use_case.execute(
            DeleteChatCommand(user_id=descriptor, chat_id=chat_id)
        )
