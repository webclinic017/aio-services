from aio_services.models import CloudEvent
from typing import Any, Protocol, TypeVar

MsgT = TypeVar("MsgT")

DataT = TypeVar("DataT", bound=CloudEvent)


class Encoder(Protocol):
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...
