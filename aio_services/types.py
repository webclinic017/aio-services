from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, TypeVar

from typing_extensions import Protocol

if TYPE_CHECKING:
    from aio_services.broker import Broker
    from aio_services.consumer import BaseConsumer
    from aio_services.models import CloudEvent

MessageT = TypeVar("MessageT")
BrokerT = TypeVar("BrokerT", bound="Broker")
EventT = TypeVar("EventT", bound="CloudEvent")

F = TypeVar("F", bound=Callable[..., Any])


ConsumerT = TypeVar("ConsumerT", bound="BaseConsumer")

HandlerT = Callable[[EventT], Awaitable[Optional[Any]]]

ExcHandler = Callable[[EventT, Exception], Awaitable]


class Encoder(Protocol):
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...
