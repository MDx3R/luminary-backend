from typing import Annotated
from uuid import UUID

from common.presentation.http.dto.response import IDResponse
from common.presentation.http.fastapi.auth import get_descriptor
from common.presentation.http.fastapi.cbv import cbv
from fastapi import APIRouter, Depends, UploadFile, status
from luminary_files.application.interfaces.services.file_service import (
    IFileService,
    UploadFileCommand,
)

from luminary.source.application.interfaces.usecases.command.create_source_use_case import (
    CreateFileSourceCommand,
    CreateLinkSourceCommand,
    CreatePageSourceCommand,
    ICreateFileSourceUseCase,
    ICreateLinkSourceUseCase,
    ICreatePageSourceUseCase,
)
from luminary.source.presentation.http.dto.request import (
    CreateFileSourceRequest,
    CreateLinkSourceRequest,
    CreatePageSourceRequest,
)


command_router = APIRouter()


@cbv(command_router)
class SourceCommandController:
    create_file_source_use_case: ICreateFileSourceUseCase = Depends()
    create_page_source_use_case: ICreatePageSourceUseCase = Depends()
    create_link_source_use_case: ICreateLinkSourceUseCase = Depends()
    file_service: IFileService = Depends()

    @command_router.post("/file", dependencies=[], status_code=status.HTTP_201_CREATED)
    async def create_file(
        self,
        file: UploadFile,
        request: Annotated[CreateFileSourceRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> IDResponse:
        file_id = await self.file_service.upload_file(
            UploadFileCommand(
                user_id=descriptor, filename=file.filename or "file", content=file.file
            )
        )
        source_id = await self.create_file_source_use_case.execute(
            CreateFileSourceCommand(
                user_id=descriptor, title=request.title, file_id=file_id
            )
        )

        return IDResponse(id=source_id)

    @command_router.post("/page", dependencies=[], status_code=status.HTTP_201_CREATED)
    async def create_page(
        self,
        page: UploadFile,
        request: Annotated[CreatePageSourceRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> IDResponse:
        source_id = await self.create_page_source_use_case.execute(
            CreatePageSourceCommand(
                user_id=descriptor, title=request.title, data=page.file
            )
        )

        return IDResponse(id=source_id)

    @command_router.post("/link", dependencies=[], status_code=status.HTTP_201_CREATED)
    async def create_link(
        self,
        request: Annotated[CreateLinkSourceRequest, Depends()],
        descriptor: Annotated[UUID, Depends(get_descriptor)],
    ) -> IDResponse:
        source_id = await self.create_link_source_use_case.execute(
            CreateLinkSourceCommand(
                user_id=descriptor, title=request.title, url=request.url
            )
        )

        return IDResponse(id=source_id)
