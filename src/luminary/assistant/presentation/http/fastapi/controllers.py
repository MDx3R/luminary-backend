from typing import Annotated
from uuid import UUID

from common.presentation.http.dto.response import IDResponse
from common.presentation.http.fastapi.auth import get_descriptor
from common.presentation.http.fastapi.cbv import cbv
from fastapi import APIRouter, Depends, status

from luminary.assistant.application.interfaces.usecases.command.create_assistant_use_case import (
    CreateAssistantCommand,
    ICreateAssistantUseCase,
)
from luminary.assistant.application.interfaces.usecases.command.delete_assistant_use_case import (
    DeleteAssistantCommand,
    IDeleteAssistantUseCase,
)
from luminary.assistant.application.interfaces.usecases.command.update_assistant_info_use_case import (
    IUpdateAssistantInfoUseCase,
    UpdateAssistantInfoCommand,
)
from luminary.assistant.application.interfaces.usecases.command.update_assistant_instructions_use_case import (
    IUpdateAssistantInstructionsUseCase,
    UpdateAssistantInstructionsCommand,
)
from luminary.assistant.presentation.http.dto.request import (
    CreateAssistantRequest,
    UpdateAssistantInfoRequest,
    UpdateAssistantInstructionsRequest,
)


command_router = APIRouter()


@cbv(command_router)
class AssistantCommandController:
    create_assistant_use_case: ICreateAssistantUseCase = Depends()
    update_assistant_info_use_case: IUpdateAssistantInfoUseCase = Depends()
    update_assistant_instructions_use_case: IUpdateAssistantInstructionsUseCase = (
        Depends()
    )
    delete_assistant_use_case: IDeleteAssistantUseCase = Depends()

    @command_router.post("/", dependencies=[], status_code=status.HTTP_201_CREATED)
    async def create(
        self,
        request: Annotated[CreateAssistantRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> IDResponse:
        assistant_id = await self.create_assistant_use_case.execute(
            CreateAssistantCommand(
                user_id=descriptor,
                name=request.name,
                description=request.description,
                prompt=request.prompt,
            )
        )
        return IDResponse(id=assistant_id)

    @command_router.put(
        "/{assistant_id:uuid}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def update_info(
        self,
        assistant_id: UUID,
        request: Annotated[UpdateAssistantInfoRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.update_assistant_info_use_case.execute(
            UpdateAssistantInfoCommand(
                user_id=descriptor,
                assistant_id=assistant_id,
                name=request.name,
                description=request.description,
            )
        )

    @command_router.put(
        "/{assistant_id:uuid}/instructions",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def update_instructions(
        self,
        assistant_id: UUID,
        request: Annotated[UpdateAssistantInstructionsRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.update_assistant_instructions_use_case.execute(
            UpdateAssistantInstructionsCommand(
                user_id=descriptor,
                assistant_id=assistant_id,
                prompt=request.prompt,
            )
        )

    @command_router.delete(
        "/{assistant_id:uuid}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete(
        self,
        assistant_id: UUID,
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> None:
        await self.delete_assistant_use_case.execute(
            DeleteAssistantCommand(
                user_id=descriptor,
                assistant_id=assistant_id,
            )
        )
