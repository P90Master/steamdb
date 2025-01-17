import abc


class IndexBackend(abc.ABC):
    @abc.abstractmethod
    async def fulltext_search(self, value: str, fields: list[str] | None = None) -> list[int]:
        """
        returns a list of app ids
        """
        ...
