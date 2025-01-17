from logging import Logger
from typing import ClassVar, Any, Optional, Type

from .types import Backend, KeyBuilder, Coder
from .key_builders import default_key_builder
from .coders import JsonCoder


class CacheManager:
    # TODO: DRY - should this be a pip package?

    _backend: ClassVar[Optional[Backend]] = None
    _prefix: ClassVar[Optional[str]] = None
    _expire: ClassVar[Optional[int]] = None
    _key_builder: ClassVar[Optional[KeyBuilder]] = None
    _coder: ClassVar[Optional[Type[Coder]]] = None
    _init: ClassVar[bool] = False
    _logger: ClassVar[Logger] = None

    @classmethod
    def init(
        cls,
        backend: Backend,
        prefix: str = "",
        expire: Optional[int] = None,
        key_builder: KeyBuilder = default_key_builder,
        coder: Type[Coder] = JsonCoder,
        logger: Optional[Logger] = None,
    ):
        if cls._init:
            return
        cls._init = True
        cls._backend = backend
        cls._prefix = prefix
        cls._expire = expire
        cls._key_builder = key_builder
        cls._coder = coder
        cls._logger = Logger('Cache') if logger is None else logger

    @classmethod
    def reset(cls) -> None:
        cls._init = False
        cls._backend = None
        cls._prefix = None
        cls._expire = None
        cls._key_builder = None
        cls._coder = None
        cls._logger = Logger('Cache')

    @classmethod
    def get_backend(cls) -> Backend:
        assert cls._backend, "You must call init first!"  # noqa: S101
        return cls._backend

    @classmethod
    def get_prefix(cls) -> str:
        assert cls._prefix is not None, "You must call init first!"  # noqa: S101
        return cls._prefix

    @classmethod
    def get_expire(cls) -> Optional[int]:
        return cls._expire

    @classmethod
    def get_key_builder(cls) -> KeyBuilder:
        assert cls._key_builder, "You must call init first!"  # noqa: S101
        return cls._key_builder

    @classmethod
    def get_coder(cls) -> Type[Coder]:
        assert cls._coder, "You must call init first!"  # noqa: S101
        return cls._coder

    @classmethod
    async def clear(
            cls,
            key: str,
            namespace: Optional[str] = None,
            key_builder: Optional[KeyBuilder] = None
    ) -> int:
        prefix = cls.get_prefix()
        backend = cls.get_backend()

        namespace = prefix + (":" + namespace if namespace else "")
        cache_key_builder = key_builder or cls.get_key_builder()

        cache_key = cache_key_builder(
            namespace,
            original_key=key
        )
        return await backend.clear(namespace, cache_key)

    @classmethod
    async def get(
            cls,
            key: str,
            namespace: str = "",
            key_builder: Optional[KeyBuilder] = None,
            coder: Optional[Type[Coder]] = None
    ) -> Optional[Any]:
        prefix = cls.get_prefix()
        backend = cls.get_backend()
        cache_key_builder = key_builder or cls.get_key_builder()
        coder = coder or cls.get_coder()
        namespace = prefix + (":" + namespace if namespace else "")

        cache_key = cache_key_builder(
            namespace,
            original_key=key
        )

        try:
            cached_bytes = await backend.get(cache_key)
            cached = coder.decode(cached_bytes) if cached_bytes else None
        except Exception:
            cls._logger.warning(
                f"Error retrieving cache key '{cache_key}' from backend:",
                exc_info=True,
            )
            cached = None

        return cached

    @classmethod
    async def save(
            cls,
            caching_obj: Any,
            key: str,
            expire: Optional[int] = None,
            namespace: str = "",
            key_builder: Optional[KeyBuilder] = None,
            coder: Optional[Type[Coder]] = None
    ):
        prefix = cls.get_prefix()
        expire = expire or cls.get_expire()
        cache_key_builder = key_builder or cls.get_key_builder()
        backend = cls.get_backend()
        coder = coder or cls.get_coder()
        namespace = prefix + (":" + namespace if namespace else "")

        cache_key = cache_key_builder(
            namespace,
            original_key=key
        )
        to_cache = coder.encode(caching_obj)

        try:
            await backend.set(cache_key, to_cache, expire)
        except Exception:
            # TODO: Backend logger
            cls._logger.warning(
                f"Error setting cache key '{cache_key}' in backend:",
                exc_info=True,
            )
            pass
