import logging
from abc import abstractmethod
from functools import cached_property
from typing import Type, Optional, Any, List, Generic, Callable, Awaitable

from aio_services.middleware import Middleware
from aio_services.models import CloudEvent
from aio_services.types import Encoder, MsgT, DataT


class MessageProxy(Generic[MsgT, DataT]):
    _data_prop = "data"
    __slots__ = ("_message", "_broker")

    def __init__(self, message: MsgT, broker: "Broker"):
        self._message = message
        self._broker = broker

    @cached_property
    def data(self) -> DataT:
        parsed = self._broker.encoder.decode(getattr(self._message, self._data_prop))
        # type annotation?
        return parsed

    @property
    def raw_message(self) -> MsgT:
        return self._message

    async def ack(self, **kwargs):
        await self._broker.dispatch_before("ack", self)
        await self._ack(**kwargs)
        await self._broker.dispatch_after("ack", self)

    async def nack(self, **kwargs):
        await self._broker.dispatch_before("nack", self)
        await self._nack(**kwargs)
        await self._broker.dispatch_after("nack", self)

    async def retry(self, **kwargs):
        ...

    async def _ack(self, **kwargs):
        ...

    async def _nack(self, **kwargs):
        ...

    def __getattr__(self, item):
        return getattr(self._message, item)


HandlerT = Callable[[MessageProxy[MsgT, DataT]], Awaitable[Optional[CloudEvent]]]


class Consumer(Generic[MsgT]):
    message_proxy_class: Type[MessageProxy[MsgT]]

    def __init__(
        self,
        group_id: str,
        topic: str,
        fn: HandlerT,
        auto_ack: bool = True,
        **options: Any,
    ):
        super().__init__()
        self.group_id = group_id
        self.topic = topic
        self.fn = fn
        self.auto_ack = auto_ack
        self.options = options
        self.logger = logging.getLogger(type(self).__name__)
        msg_type = fn.__annotations__.get("message")
        if not msg_type:
            raise ValueError(f"Function {fn.__name__} must have 1 argument 'message'")
        try:
            self.event_type = msg_type.__args__[0]  # type: ignore
        except IndexError:
            raise ValueError("Message must have annotated event type")

    @abstractmethod
    async def _consume(self, broker) -> None:
        raise NotImplementedError

    async def consume(self, broker):
        await broker.dispatch_before("consumer_start", broker, self)
        await self._consume(broker)
        await broker.dispatch_after("consumer_start", broker, self)

    async def _process_message(self, broker, message):
        message = self.message_proxy_class(broker, message)
        await broker.dispatch_before("process_message", message)
        exc = None
        try:
            await self.fn(message)
            if self.auto_ack:
                await message.ack()
        except Exception as e:
            exc = e
        await broker.dispatch_after("process_message", message, exc)


class ConsumerGroup(Generic[MsgT]):
    @property
    @abstractmethod
    def consumer_class(self) -> Type[Consumer[MsgT]]:
        # TODO: get default from type(self).__args__[0]
        raise NotImplementedError

    def __init__(self, group_id: str):
        self.group_id = group_id
        self.subscribers: List[Consumer[MsgT]] = []

    def subscribe(self, topic: str, **kwargs):
        def wrapper(func):
            self.subscribers.append(
                self.consumer_class(
                    group_id=self.group_id, topic=topic, fn=func, **kwargs
                )
            )
            return func

        return wrapper


class Broker(ConsumerGroup[MsgT]):
    def __init__(
        self,
        *,
        group_id: str,
        encoder: Optional[Encoder] = None,
        middlewares: Optional[List[Middleware]] = None,
        **options,
    ):
        super().__init__(group_id)
        if encoder is None:
            from aio_services.encoders import get_default_encoder

            encoder = get_default_encoder()
        self.encoder = encoder
        self.middlewares = middlewares or []
        self.options = options
        self.logger = logging.getLogger(type(self).__name__)

    @abstractmethod
    async def _publish(self, topic: str, message, **kwargs):
        raise NotImplementedError

    async def publish(self, topic: str, message, **kwargs):
        await self.dispatch_before("publish", self, topic, message)
        data = self.encoder.encode(message)
        await self._publish(topic, data, **kwargs)
        await self.dispatch_after("publish", self, topic, message)

    def add_consumer_group(self, other: ConsumerGroup[MsgT]):
        assert (
            self.consumer_class == other.consumer_class
        ), "Consumer Groups must be in the same class"
        self.subscribers.extend(other.subscribers)

    def add_middleware(self, middleware: Middleware):
        self.middlewares.append(middleware)

    async def _dispatch(self, full_event: str, *args, **kwargs) -> None:
        for m in self.middlewares:
            try:
                await getattr(m, full_event)(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Unhandled middleware exception {e}")

    async def dispatch_before(self, event: str, *args, **kwargs):
        await self._dispatch(f"before_{event}", *args, **kwargs)

    async def dispatch_after(self, event: str, *args, **kwargs):
        await self._dispatch(f"after_{event}", *args, **kwargs)
