import json
from typing import Any

from .types import Coder


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> Any:
        return json.dumps(value).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return json.loads(json.loads(value.decode()))
