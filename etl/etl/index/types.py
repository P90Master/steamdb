import abc
from typing import Any


class IndexBackend:
    @abc.abstractmethod
    def bulk_update(self, apps: list[dict[str, Any]]):
        ...
