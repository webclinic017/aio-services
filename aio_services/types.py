from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Protocol, TypeVar


if TYPE_CHECKING:
    from aio_services.models import BaseConsumerOptions, CloudEvent
    from aio_services.broker import Broker
    from aio_services.consumer import BaseConsumer

MessageT = TypeVar("MessageT")
EventT = TypeVar("EventT", bound="CloudEvent")
COpts = TypeVar("COpts", bound="BaseConsumerOptions")
F = TypeVar("F", bound=Callable[..., Any])

BrokerT = TypeVar("BrokerT", bound="Broker")

ConsumerT = TypeVar("ConsumerT", bound="BaseConsumer")

HandlerT = Callable[[EventT], Awaitable[Optional[Any]]]

ExcHandler = Callable[[EventT, Exception], Awaitable]


class Encoder(Protocol):
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...
