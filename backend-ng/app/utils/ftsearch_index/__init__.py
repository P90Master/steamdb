from typing import ClassVar

from .types import IndexBackend
from .backends.elasticsearch import ElasticsearchIndexBackend


class Index:
    _backend: ClassVar[IndexBackend | None] = None
    _init: ClassVar[bool] = False

    @classmethod
    def init(
            cls,
            backend: IndexBackend,
    ):
        if cls._init:
            return
        cls._init = True
        cls._backend = backend

    @classmethod
    def reset(cls) -> None:
        cls._init = False
        cls._backend = None

    @classmethod
    def get_backend(cls) -> IndexBackend:
        assert cls._backend, "You must call init first!"  # noqa: S101
        return cls._backend

    @classmethod
    async def fulltext_search(cls, value: str, fields: list[str] | None = None) -> list[int]:
        backend = cls.get_backend()
        return await backend.fulltext_search(value, fields)
