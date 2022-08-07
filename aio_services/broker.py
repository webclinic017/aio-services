from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, Generic

from aio_services.exceptions import Skip

from aio_services.utils.mixins import ConsumerOptMixin, LoggerMixin
from aio_services.types import MessageT, COpts

if TYPE_CHECKING:
    from aio_services.consumer import Consumer
    from aio_services.middleware import Middleware
    from aio_services.types import Encoder, EventT


class Broker(ABC, LoggerMixin, ConsumerOptMixin[COpts], Generic[COpts, MessageT]):
    def __init__(
        self,
        *,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options,
    ) -> None:
        if encoder is None:
            from aio_services.encoders import get_default_encoder

            encoder = get_default_encoder()

        self.encoder = encoder
        middlewares = middlewares or []
        # for m in middlewares:
        #     if not issubclass(type(self), m.broker_class):
        #         raise TypeError(
        #             f"Invalid broker/middleware combination. "
        #             f"Expected {m.broker_class}. Got {type(self)}"
        #         )
        self.middlewares = middlewares
        self.options = options

    def parse_incoming_message(self, message: MessageT, type_: EventT) -> EventT:
        raw_data = self.get_message_data(message)
        decoded = self.encoder.decode(data=raw_data)
        data = type_.parse_obj(decoded)
        return data

    @staticmethod
    @abstractmethod
    def get_message_data(message: MessageT) -> bytes:
        raise NotImplementedError

    def get_handler(self, consumer: Consumer) -> Callable[[MessageT], Awaitable[None]]:
        async def handler(message: MessageT) -> None:
            exc = None
            result = None
            event = self.parse_incoming_message(message, consumer.event_type)
            await self.dispatch_before("process_message", event, message)
            try:
                result = await consumer.process(event)
            except Skip:
                self.logger.info(f"Skipped message {event.id}")
                await self.dispatch_after("skip_message", event, message)
            # TODO: asyncio.CanceledError handling?
            except Exception as e:
                exc = e
            finally:
                await self.dispatch_after(
                    "process_message", event, message, result, exc
                )
                await self.ack(consumer, message)

        return handler

    async def ack(self, consumer: Consumer, message: MessageT) -> None:
        await self.dispatch_before("ack", consumer, message)
        await self._ack(message)
        await self.dispatch_after("ack", consumer, message)

    async def connect(self) -> None:
        await self.dispatch_before("broker_connect")
        await self._connect()
        await self.dispatch_after("broker_connect")

    async def disconnect(self) -> None:
        await self.dispatch_before("broker_disconnect")
        await self._disconnect()
        await self.dispatch_after("broker_disconnect")

    async def publish(self, message: EventT, **kwargs) -> None:
        await self.dispatch_before("publish", self, message)
        await self._publish(message, **kwargs)
        await self.dispatch_after("publish", self, message)

    async def start_consumer(self, consumer: Consumer):
        await self.dispatch_before("consumer_start", consumer)
        await self._start_consumer(consumer)
        await self.dispatch_after("consumer_start", consumer)

    def add_middleware(self, middleware: Middleware) -> None:
        if not isinstance(middleware, Middleware):
            raise TypeError(f"Middleware expected, got {type(middleware)}")
        # if not issubclass(type(self), middleware.supported_brokers):
        #     raise TypeError(
        #         f"Invalid broker/middleware combination. "
        #         f"Expected one of: {middleware.supported_brokers}. Got {type(self)}"
        #     )
        self.middlewares.append(middleware)

    async def _dispatch(self, full_event: str, *args, **kwargs) -> None:
        for m in self.middlewares:
            try:
                await getattr(m, full_event)(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Unhandled middleware exception {e}")

    async def dispatch_before(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"before_{event}", *args, **kwargs)

    async def dispatch_after(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"after_{event}", *args, **kwargs)

    # broker specific implementations below

    @abstractmethod
    async def _publish(self, message: EventT, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _start_consumer(self, consumer: Consumer) -> None:
        raise NotImplementedError

    async def _ack(self, message: MessageT) -> None:
        """There is empty default body, because some brokers don't have ack"""
