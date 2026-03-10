"""Read repository implementation for Assistant: ORM -> read models."""

from collections.abc import Sequence
from uuid import UUID

from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from sqlalchemy import select

from luminary.assistant.application.dtos.read_models import (
    AssistantReadModel,
    AssistantSummaryReadModel,
)
from luminary.assistant.application.interfaces.repositories.assistant_read_repository import (
    IAssistantReadRepository,
)
from luminary.assistant.infrastructure.database.postgres.sqlalchemy.models.assistant_base import (
    AssistantBase,
)


class AssistantReadRepository(IAssistantReadRepository):
    def __init__(self, executor: QueryExecutor) -> None:
        self._executor = executor

    async def get_by_id(self, assistant_id: UUID, owner_id: UUID) -> AssistantReadModel:
        stmt = (
            select(AssistantBase)
            .where(AssistantBase.assistant_id == assistant_id)
            .where(AssistantBase.owner_id == owner_id)
            .where(AssistantBase.is_active)
        )
        row = await self._executor.execute_scalar_one(stmt)
        if not row:
            raise NotFoundError(str(assistant_id))
        return AssistantReadModel(
            id=row.assistant_id,
            name=row.name,
            description=row.description,
            type=row.type.value,
            prompt=row.prompt,
            created_at=row.created_at,
        )

    async def list_by_owner(
        self, owner_id: UUID
    ) -> Sequence[AssistantSummaryReadModel]:
        stmt = (
            select(AssistantBase)
            .where(AssistantBase.owner_id == owner_id)
            .where(AssistantBase.is_active)
            .order_by(AssistantBase.created_at.desc())
        )
        rows = await self._executor.execute_scalar_many(stmt)
        return [
            AssistantSummaryReadModel(
                id=r.assistant_id,
                name=r.name,
                description=r.description,
                type=r.type.value,
            )
            for r in rows
        ]
