"""Lecturer bounded context DI container."""

from typing import Any

from dependency_injector import containers, providers

from luminary.source.application.policies.source_access_policy import SourceAccessPolicy
from luminary.source.application.repositories.source_repository import (
    EventBusSourceRepository,
)
from luminary.source.application.usecases.command.create_source_use_case import (
    CreateFileSourceUseCase,
    CreateLinkSourceUseCase,
    CreatePageSourceUseCase,
)
from luminary.source.application.usecases.command.delete_source_use_case import (
    DeleteSourceUseCase,
)
from luminary.source.application.usecases.command.update_source_use_case import (
    UpdateSourceUseCase,
)
from luminary.source.domain.factories.source_factory import SourceFactory
from luminary.source.infrastructure.database.postgres.sqlalchemy.repositories.source_repository import (
    SourceRepository,
)


class SourceContainer(containers.DeclarativeContainer):
    """Dependency injection container for source bounded context."""

    # Explicit dependency declarations
    clock: providers.Dependency[Any] = providers.Dependency()
    uuid_generator: providers.Dependency[Any] = providers.Dependency()
    query_executor: providers.Dependency[Any] = providers.Dependency()

    unit_of_work: providers.Dependency[Any] = providers.Dependency()
    event_bus: providers.Dependency[Any] = providers.Dependency()

    # Domain services
    source_factory = providers.Singleton(
        SourceFactory, clock=clock, uuid_generator=uuid_generator
    )

    # Write repository
    source_repository = providers.Singleton(SourceRepository, query_executor)
    event_bus_source_repository = providers.Singleton(
        EventBusSourceRepository,
        uow=unit_of_work,
        event_bus=event_bus,
        repository=source_repository,
    )

    # Access policy
    source_access_policy = providers.Singleton(SourceAccessPolicy)

    # Write use cases
    create_file_source_use_case = providers.Singleton(
        CreateFileSourceUseCase,
        source_factory=event_bus_source_repository,
        source_repository=source_repository,
    )
    create_link_source_use_case = providers.Singleton(
        CreateLinkSourceUseCase,
        source_factory=event_bus_source_repository,
        source_repository=source_repository,
    )
    create_page_source_use_case = providers.Singleton(
        CreatePageSourceUseCase,
        source_factory=event_bus_source_repository,
        source_repository=source_repository,
    )

    update_source_use_case = providers.Singleton(
        UpdateSourceUseCase,
        repository=event_bus_source_repository,
        access_policy=source_access_policy,
    )

    delete_source_use_case = providers.Singleton(
        DeleteSourceUseCase,
        repository=event_bus_source_repository,
        access_policy=source_access_policy,
    )
