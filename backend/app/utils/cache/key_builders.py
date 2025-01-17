import hashlib
from typing import Any


def default_key_builder(
        __namespace: str = "",
        *args: tuple[Any, ...],
        original_key: str,
        **kwargs: dict[str, Any]
) -> str:
    cache_key = hashlib.md5(original_key.encode()).hexdigest()
    return f"{__namespace}:{cache_key}"
