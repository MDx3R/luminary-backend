"""Folder bounded context DI container."""

from typing import Any

from dependency_injector import containers, providers

from luminary.folder.application.policies.folder_access_policy import (
    FolderAccessPolicy,
)
from luminary.folder.application.repositories.folder_repository import (
    EventBusFolderRepository,
)
from luminary.folder.application.usecases.command.add_source_to_folder_use_case import (
    AddSourceToFolderUseCase,
)
from luminary.folder.application.usecases.command.change_folder_assistant_use_case import (
    ChangeFolderAssistantUseCase,
)
from luminary.folder.application.usecases.command.create_folder_chat_use_case import (
    CreateFolderChatUseCase,
)
from luminary.folder.application.usecases.command.create_folder_use_case import (
    CreateFolderUseCase,
)
from luminary.folder.application.usecases.command.delete_folder_use_case import (
    DeleteFolderUseCase,
)
from luminary.folder.application.usecases.command.remove_chat_from_folder_use_case import (
    RemoveChatFromFolderUseCase,
)
from luminary.folder.application.usecases.command.remove_folder_assistant_use_case import (
    RemoveFolderAssistantUseCase,
)
from luminary.folder.application.usecases.command.remove_source_from_folder_use_case import (
    RemoveSourceFromFolderUseCase,
)
from luminary.folder.application.usecases.command.update_editor_content_use_case import (
    UpdateEditorContentUseCase,
)
from luminary.folder.application.usecases.command.update_folder_info_use_case import (
    UpdateFolderInfoUseCase,
)
from luminary.folder.domain.factories.folder_factory import FolderFactory
from luminary.folder.infrastructure.database.postgres.sqlalchemy.repositories.folder_repository import (
    FolderRepository,
)


class FolderContainer(containers.DeclarativeContainer):
    """Dependency injection container for folder bounded context."""

    clock: providers.Dependency[Any] = providers.Dependency()
    uuid_generator: providers.Dependency[Any] = providers.Dependency()
    query_executor: providers.Dependency[Any] = providers.Dependency()
    unit_of_work: providers.Dependency[Any] = providers.Dependency()
    event_bus: providers.Dependency[Any] = providers.Dependency()
    chat_factory: providers.Dependency[Any] = providers.Dependency()
    chat_repository: providers.Dependency[Any] = providers.Dependency()

    folder_factory = providers.Singleton(
        FolderFactory, clock=clock, uuid_generator=uuid_generator
    )

    folder_repository = providers.Singleton(FolderRepository, query_executor)
    event_bus_folder_repository = providers.Singleton(
        EventBusFolderRepository,
        uow=unit_of_work,
        event_bus=event_bus,
        repository=folder_repository,
    )

    folder_access_policy = providers.Singleton(FolderAccessPolicy)

    create_folder_use_case = providers.Singleton(
        CreateFolderUseCase,
        folder_factory=folder_factory,
        folder_repository=event_bus_folder_repository,
    )
    update_folder_info_use_case = providers.Singleton(
        UpdateFolderInfoUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    delete_folder_use_case = providers.Singleton(
        DeleteFolderUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    change_folder_assistant_use_case = providers.Singleton(
        ChangeFolderAssistantUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    remove_folder_assistant_use_case = providers.Singleton(
        RemoveFolderAssistantUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    add_source_to_folder_use_case = providers.Singleton(
        AddSourceToFolderUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    remove_source_from_folder_use_case = providers.Singleton(
        RemoveSourceFromFolderUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    create_folder_chat_use_case = providers.Singleton(
        CreateFolderChatUseCase,
        uow=unit_of_work,
        folder_repository=event_bus_folder_repository,
        chat_factory=chat_factory,
        chat_repository=chat_repository,
        access_policy=folder_access_policy,
    )
    remove_chat_from_folder_use_case = providers.Singleton(
        RemoveChatFromFolderUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
    )
    update_editor_content_use_case = providers.Singleton(
        UpdateEditorContentUseCase,
        repository=event_bus_folder_repository,
        access_policy=folder_access_policy,
        clock=clock,
    )
