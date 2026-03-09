from abc import ABC, abstractmethod

from luminary.assistant.domain.entity.assistant import AssistantId
from luminary.folder.domain.entity.folder import Folder
from luminary.folder.domain.value_objects.folder_id import FolderId


class IFolderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: FolderId) -> Folder: ...

    @abstractmethod
    async def add(self, entity: Folder) -> None: ...

    @abstractmethod
    async def save(self, entity: Folder) -> None: ...

    @abstractmethod
    async def clear_assistant_reference(self, assistant_id: AssistantId) -> None: ...
