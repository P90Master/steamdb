import json
from typing import Any

from .types import Coder


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> Any:
        return json.dumps(value).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        first_layer = json.loads(value.decode())
        if isinstance(first_layer, dict):
            return first_layer

        return json.loads(first_layer)
