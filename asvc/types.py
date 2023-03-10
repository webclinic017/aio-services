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

from typing_extensions import Protocol, TypedDict

if TYPE_CHECKING:
    from asvc import CloudEvent, GenericConsumer


RawMessage = TypeVar("RawMessage")

T = TypeVar("T", bound="CloudEvent")
D = TypeVar("D", bound=Any)


class TagMeta(TypedDict):
    name: str
    description: str


class Encoder(Protocol):
    CONTENT_TYPE: str

    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...


FT = Callable[["CloudEvent"], Awaitable[Optional[Any]]]
MessageHandlerT = Union[Type["GenericConsumer"], FT]

ExcHandler = Callable[["CloudEvent", Exception], Awaitable]
