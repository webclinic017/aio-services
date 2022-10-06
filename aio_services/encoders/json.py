import json
from typing import Any

from pydantic.json import pydantic_encoder

from aio_services.exceptions import DecodeError


class JsonEncoder:
    @staticmethod
    def encode(data: Any) -> bytes:
        return json.dumps(data, default=pydantic_encoder).encode("utf-8")

    @staticmethod
    def decode(data: bytes) -> Any:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise DecodeError(data=data, error=e)
