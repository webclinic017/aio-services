from typing import Any, Awaitable, Callable, Optional, Protocol, TypeVar, Union

from aio_services.broker import Broker
from aio_services.models import BaseConsumerOptions, CloudCommand, CloudEvent

BrokerT = TypeVar("BrokerT", bound=Broker)

COpts = TypeVar("COpts", bound=BaseConsumerOptions)
MessageT = TypeVar("MessageT")
EventT = TypeVar("EventT", bound=Union[CloudEvent, CloudCommand])

HandlerT = Callable[[EventT], Awaitable[Optional[Any]]]

F = TypeVar("F", bound=Callable[..., Any])


class Encoder(Protocol):
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...
