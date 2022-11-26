from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Optional,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from typing_extensions import Protocol

if TYPE_CHECKING:
    from asvc.consumer import GenericConsumer
    from asvc.models import CloudEvent

UUIDStr = Union[UUID, str]

RawMessage = TypeVar("RawMessage")

T = TypeVar("T", bound="CloudEvent")


class Encoder(Protocol):
    CONTENT_TYPE: str

    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...


FT = Callable[["CloudEvent"], Awaitable[Optional[Any]]]
MessageHandlerT = Union[Type["GenericConsumer"], FT]

ExcHandler = Callable[["CloudEvent", Exception], Awaitable]
