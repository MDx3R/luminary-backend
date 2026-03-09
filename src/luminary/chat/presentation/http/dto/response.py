from typing import Self
from uuid import UUID

from pydantic import BaseModel

from luminary.chat.application.interfaces.usecases.command.get_message_response_use_case import (
    StreamingMessageDTO,
    StreamState,
)
from luminary.chat.domain.enums import Author, MessageStatus


class StreamingMessageResponse(BaseModel):
    message_id: UUID
    state: StreamState
    content: str
    author: Author
    status: MessageStatus

    @classmethod
    def from_dto(cls, dto: StreamingMessageDTO) -> Self:
        return cls(
            message_id=dto.message_id,
            state=dto.state,
            content=dto.content,
            author=dto.author,
            status=dto.status,
        )
