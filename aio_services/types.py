from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

if TYPE_CHECKING:
    from aio_services.broker import BaseBroker


BrokerT = TypeVar("BrokerT", bound="BaseBroker")

RawMessage = TypeVar("RawMessage")
T = TypeVar("T")


class Encoder(Protocol):
    CONTENT_TYPE: str

    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...


class AbstractMessage(Protocol[T]):
    version: str
    content_type: str
    id: UUID | str
    trace_id: UUID | str
    topic: str
    type: str
    source: str | None
    data: T
    time: datetime

    def dict(self, **kwargs) -> dict[str, Any]:
        ...


class AbstractIncomingMessage(AbstractMessage[T], Generic[T, RawMessage]):
    raw: RawMessage


IncomingMessage = TypeVar("IncomingMessage", bound=AbstractIncomingMessage)


@dataclass
class Response:
    topic: str
    type: str = "CloudEvent"


class ConsumerP(Protocol[IncomingMessage, T]):
    name: str
    service_name: str
    topic: str
    event_type: T
    timeout: int | float
    response: Response | None
    dynamic: bool
    options: dict[str, Any]

    full_name: str  # qualname?

    async def process(self, message: AbstractIncomingMessage[T, RawMessage]):
        ...

    def validate_message(self, data: Any) -> T:
        ...


FT = Callable[[AbstractIncomingMessage], Awaitable[Optional[Any]]]
MessageHandlerT = Union[Type[ConsumerP], FT]

ExcHandler = Callable[[AbstractIncomingMessage, Exception], Awaitable]
