import pickle
from typing import Any


class PickleEncoder:
    @staticmethod
    def encode(data: Any) -> bytes:
        return pickle.dumps(data)

    @staticmethod
    def decode(data: bytes) -> Any:
        return pickle.loads(data)
