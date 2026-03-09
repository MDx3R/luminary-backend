from common.domain.value_objects.datetime import DateTime
from common.domain.value_objects.id import UserId

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.chat.domain.value_objects.chat_id import ChatId
from luminary.folder.domain.entity.folder import Folder
from luminary.folder.domain.value_objects.editor_content import EditorContent
from luminary.folder.domain.value_objects.folder_id import FolderId
from luminary.folder.domain.value_objects.folder_info import FolderInfo
from luminary.folder.infrastructure.database.postgres.sqlalchemy.models.folder_base import (
    FolderBase,
    FolderChatAssociation,
    FolderSourceAssociation,
)
from luminary.source.domain.entity.source import SourceId


class FolderMapper:
    @classmethod
    def to_domain(cls, base: FolderBase) -> Folder:
        assistant_id = AssistantId.optional(base.assistant_id)
        editor_content = None
        if base.editor_text is not None and base.editor_updated_at is not None:
            editor_content = EditorContent(
                text=base.editor_text,
                updated_at=DateTime(base.editor_updated_at),
            )

        chats = {ChatId(c.chat_id) for c in base.chat_associations}
        sources = {SourceId(s.source_id) for s in base.source_associations}

        return Folder(
            id=FolderId(base.folder_id),
            owner_id=UserId(base.owner_id),
            info=FolderInfo(name=base.name, description=base.description),
            assistant_id=assistant_id,
            created_at=DateTime(base.created_at),
            is_deleted=base.is_deleted,
            _chats=chats,
            _sources=sources,
            editor_content=editor_content,
        )

    @classmethod
    def to_persistence(cls, folder: Folder) -> FolderBase:
        folder_id = folder.id.value

        editor_text = None
        editor_updated_at = None
        if folder.editor_content is not None:
            editor_text = folder.editor_content.text
            editor_updated_at = folder.editor_content.updated_at.value

        chats = [
            FolderChatAssociation(folder_id=folder_id, chat_id=cid.value)
            for cid in folder.chats
        ]
        sources = [
            FolderSourceAssociation(folder_id=folder_id, source_id=sid.value)
            for sid in folder.sources
        ]

        return FolderBase(
            folder_id=folder_id,
            owner_id=folder.owner_id.value,
            name=folder.info.name,
            description=folder.info.description,
            assistant_id=(folder.assistant_id.value if folder.assistant_id else None),
            editor_text=editor_text,
            editor_updated_at=editor_updated_at,
            created_at=folder.created_at.value,
            updated_at=folder.created_at.value,
            is_deleted=folder.is_deleted,
            chat_associations=chats,
            source_associations=sources,
        )
