from common.application.exceptions import NotFoundError
from common.infrastructure.database.sqlalchemy.executor import QueryExecutor
from sqlalchemy import delete, select

from luminary.chat.application.interfaces.repositories.message_repository import (
    IMessageRepository,
)
from luminary.chat.domain.entity.message import Message
from luminary.chat.domain.value_objects.message_id import MessageId
from luminary.chat.infrastructure.database.postgres.sqlalchemy.mappers.message_mapper import (
    MessageMapper,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.attachment_base import (
    AttachmentBase,
)
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.message_base import (
    MessageBase,
)


class MessageRepository(IMessageRepository):
    def __init__(self, executor: QueryExecutor) -> None:
        self.executor = executor

    async def get_by_id(self, id: MessageId) -> Message:
        stmt = (
            select(MessageBase, AttachmentBase)
            .select_from(MessageBase)
            .outerjoin(
                AttachmentBase,
                MessageBase.message_id == AttachmentBase.message_id,
            )
            .where(MessageBase.message_id == id.value)
        )
        rows = await self.executor.execute_many(stmt)
        if not rows:
            raise NotFoundError(id)
        base = rows[0][0]
        attachments = [row[1] for row in rows if row[1] is not None]
        return MessageMapper.to_domain(base, attachments)

    async def add(self, entity: Message) -> None:
        base = MessageMapper.to_persistence(entity)
        await self.executor.add(base)
        for att in entity.attachments:
            att_base = AttachmentBase(
                message_id=entity.id.value,
                name=att.name,
                content_id=att.content_id,
                source_id=att.source_id.value if att.source_id else None,
            )
            await self.executor.add(att_base)

    async def save(self, entity: Message) -> None:
        base = MessageMapper.to_persistence(entity)
        await self.executor.save(base)
        await self.executor.execute(
            delete(AttachmentBase).where(
                AttachmentBase.message_id == entity.id.value
            )
        )
        for att in entity.attachments:
            att_base = AttachmentBase(
                message_id=entity.id.value,
                name=att.name,
                content_id=att.content_id,
                source_id=att.source_id.value if att.source_id else None,
            )
            await self.executor.add(att_base)

    async def remove(self, entity: Message) -> None:
        await self.executor.execute(
            delete(AttachmentBase).where(
                AttachmentBase.message_id == entity.id.value
            )
        )
        stmt = select(MessageBase).where(
            MessageBase.message_id == entity.id.value
        )
        base = await self.executor.execute_scalar_one(stmt)
        if base is not None:
            await self.executor.delete(base)
