import json
from typing import Any

from pydantic.json import pydantic_encoder


class JsonEncoder:
    @staticmethod
    def encode(data: Any) -> bytes:
        return json.dumps(data, default=pydantic_encoder).encode("utf-8")

    @staticmethod
    def decode(data: bytes) -> Any:
        return json.loads(data)
