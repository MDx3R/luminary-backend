"""Lecturer bounded context DI container."""

from typing import Any

from dependency_injector import containers, providers
from luminary_files.application.services.file_service import FileService
from luminary_files.domain.factories.file_factory import FileFactory
from luminary_files.domain.policies.extenstion_policy import MIMEWhitelistPolicy
from luminary_files.infrastructure.database.postgres.sqlalchemy.repositories.file_repository import (
    FileRepository,
)
from luminary_files.infrastructure.services.file_type_introspector import (
    FileTypeIntrospector,
)
from luminary_files.infrastructure.storage.minio.repositories.file_storage import (
    MinioFileStorage,
)


class FileContainer(containers.DeclarativeContainer):
    """Dependency injection container for file bounded context."""

    # Explicit dependency declarations

    clock: providers.Dependency[Any] = providers.Dependency()
    uuid_generator: providers.Dependency[Any] = providers.Dependency()
    query_executor: providers.Dependency[Any] = providers.Dependency()

    storage: providers.Dependency[Any] = providers.Dependency()

    allowed_mime_types: providers.Dependency[Any] = providers.Dependency()

    # Domain services
    mime_policy = providers.Singleton(MIMEWhitelistPolicy, allowed=allowed_mime_types)
    file_factory = providers.Singleton(
        FileFactory, clock=clock, uuid_generator=uuid_generator, mime_policy=mime_policy
    )

    # Write repository
    file_repository = providers.Singleton(FileRepository, query_executor)

    # Storage
    file_storage = providers.Singleton(
        MinioFileStorage, client=storage, bucket_name=FileService.BUCKET_NAME
    )

    # Other dependencies
    file_type_instorspector = providers.Singleton(FileTypeIntrospector)

    # Services
    file_service = providers.Singleton(
        FileService,
        file_factory=file_factory,
        file_type_instorspector=file_type_instorspector,
        file_repository=file_repository,
        file_storage=file_storage,
    )
