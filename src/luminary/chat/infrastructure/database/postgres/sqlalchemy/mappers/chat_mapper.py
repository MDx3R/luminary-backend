from common.domain.value_objects.datetime import DateTime
from common.domain.value_objects.id import UserId

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.chat.domain.entity.chat import Chat
from luminary.chat.domain.value_objects.chat_id import ChatId
from luminary.chat.domain.value_objects.chat_info import ChatInfo
from luminary.chat.domain.value_objects.chat_settings import ChatSettings
from luminary.chat.infrastructure.database.postgres.sqlalchemy.models.chat_base import (
    ChatBase,
    ChatSourceAssociation,
)
from luminary.folder.domain.value_objects.folder_id import FolderId
from luminary.model.domain.entity.model import ModelId
from luminary.source.domain.entity.source import SourceId


class ChatMapper:
    @classmethod
    def to_domain(cls, base: ChatBase) -> Chat:
        folder_id = FolderId(base.folder_id) if base.folder_id is not None else None
        assistant_id = AssistantId(base.assistant_id) if base.assistant_id else None
        sources = {SourceId(s.source_id) for s in base.source_associations}

        return Chat(
            id=ChatId(base.chat_id),
            owner_id=UserId(base.owner_id),
            folder_id=folder_id,
            info=ChatInfo(name=base.name),
            assistant_id=assistant_id,
            settings=ChatSettings(
                model_id=ModelId(base.model_id),
                max_context_messages=base.max_context_messages,
            ),
            created_at=DateTime(base.created_at),
            is_deleted=base.is_deleted,
            _sources=sources,
        )

    @classmethod
    def to_persistence(cls, chat: Chat) -> ChatBase:
        chat_id = chat.id.value

        sources = [
            ChatSourceAssociation(chat_id=chat_id, source_id=sid.value)
            for sid in chat.sources
        ]

        return ChatBase(
            chat_id=chat_id,
            owner_id=chat.owner_id.value,
            folder_id=chat.folder_id.value if chat.folder_id else None,
            name=chat.info.name,
            assistant_id=(chat.assistant_id.value if chat.assistant_id else None),
            model_id=chat.settings.model_id.value,
            max_context_messages=chat.settings.max_context_messages,
            created_at=chat.created_at.value,
            updated_at=chat.created_at.value,
            is_deleted=chat.is_deleted,
            source_associations=sources,
        )
