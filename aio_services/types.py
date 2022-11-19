from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from aio_services.consumer import GenericConsumer
    from aio_services.models import CloudEvent

UUIDStr = Union[UUID, str]

RawMessage = TypeVar("RawMessage")

T = TypeVar("T", bound=BaseModel)


class Encoder(Protocol):
    CONTENT_TYPE: str

    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...


FT = Callable[["CloudEvent"], Awaitable[Optional[Any]]]
MessageHandlerT = Union[Type["GenericConsumer"], FT]

ExcHandler = Callable[["CloudEvent", Exception], Awaitable]
