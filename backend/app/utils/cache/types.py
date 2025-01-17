import abc
from typing_extensions import Protocol
from typing import Any, Optional


class Backend(abc.ABC):
    @abc.abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        raise NotImplementedError


class KeyBuilder(Protocol):
    def __call__(
        self,
        __namespace: str = ...,
        *args: tuple[Any, ...],
        original_key: str = ...,
        **kwargs: dict[str, Any],
    ) -> str:
        ...


class Coder:
    @classmethod
    def encode(cls, value: Any) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError
