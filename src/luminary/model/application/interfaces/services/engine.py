from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


@dataclass(frozen=True)
class EngineStreamingResponse:
    content: str


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class MessageDTO:
    content: str
    role: Role


class IInferenceEngine(ABC):
    @abstractmethod
    def send(
        self,
        query: str,
        *,
        system_prompt: str,
        source_ids: list[UUID],
        history: list[MessageDTO],
    ) -> AsyncGenerator[EngineStreamingResponse, None]: ...
