import abc


class StateStorageBackend(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str) -> str | None:
        ...

    @abc.abstractmethod
    def set(self, key: str, value: str):
        ...
