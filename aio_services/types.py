from typing import Any, Awaitable, Callable, Optional, Protocol, TypeVar, TYPE_CHECKING


from aio_services.models import BaseConsumerOptions, CloudEvent

if TYPE_CHECKING:
    from aio_services.broker import Broker

BrokerT = TypeVar("BrokerT", bound="Broker")

COpts = TypeVar("COpts", bound=BaseConsumerOptions)
MessageT = TypeVar("MessageT")
EventT = TypeVar("EventT", bound=CloudEvent)

HandlerT = Callable[[EventT], Awaitable[Optional[Any]]]

F = TypeVar("F", bound=Callable[..., Any])


class Encoder(Protocol):
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...
