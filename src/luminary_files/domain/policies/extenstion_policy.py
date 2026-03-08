from collections.abc import Iterable

from luminary_files.domain.interfaces.extenstion_policy import (
    IMIMEPolicy,
)


class MIMEWhitelistPolicy(IMIMEPolicy):
    def __init__(self, allowed: Iterable[str]) -> None:
        self._allowed = {ext.lower() for ext in allowed}

    def is_allowed(self, extension: str) -> bool:
        return extension.lower() in self._allowed
