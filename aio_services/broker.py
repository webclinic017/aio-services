from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, Generic

import async_timeout

from aio_services.exceptions import Reject, Skip
from aio_services.logger import LoggerMixin
from aio_services.middleware import Middleware
from aio_services.middlewares import default_middlewares
from aio_services.types import MessageT

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, Encoder, EventT


class Broker(ABC, Generic[MessageT], LoggerMixin):
    def __init__(
        self,
        *,
        encoder: Encoder | None = None,
        middlewares: list[Middleware[BrokerT]] | None = None,
        **options,
    ) -> None:
        if encoder is None:
            from aio_services.encoders import get_default_encoder

            encoder = get_default_encoder()

        self.encoder = encoder
        self.middlewares = []

        if middlewares is None:
            middlewares = [m() for m in default_middlewares]

        for m in middlewares:
            self.add_middleware(m)

        self.options = options

    def parse_incoming_message(self, message: MessageT, type_: EventT) -> EventT:
        raw_data = self.get_message_data(message)
        decoded = self.encoder.decode(data=raw_data)
        data = type_.parse_obj(decoded)
        return data

    def get_handler(self, consumer: ConsumerT) -> Callable[[MessageT], Awaitable[None]]:
        async def handler(message: MessageT) -> None:
            exc = None
            result = None
            event = self.parse_incoming_message(message, consumer.event_type)
            try:
                await self.dispatch_before("process_message", consumer, event, message)
            except Skip:
                self.logger.info(f"Skipped message {event.id}")
                await self.dispatch_after("skip_message", event, message)
                await self.ack(consumer, event, message)
                return
            try:
                async with async_timeout.timeout(consumer.timeout):
                    result = await consumer.process(event)

            # TODO: asyncio.CanceledError handling (?)
            except Reject as e:
                exc = e
                self.logger.error(f"Message {event.id} rejected. {e}")
            except Exception as e:
                exc = e
            finally:
                await self.dispatch_after(
                    "process_message", event, message, result, exc
                )
                if exc and isinstance(exc, Reject):
                    await self.nack(consumer, event, message)
                else:
                    await self.ack(consumer, event, message)

        return handler

    async def ack(
        self, consumer: ConsumerT, message: EventT, raw_message: MessageT
    ) -> None:
        await self.dispatch_before("ack", consumer, message, raw_message)
        await self._ack(raw_message)
        await self.dispatch_after("ack", consumer, message, raw_message)

    async def nack(
        self,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        delay: int | None = None,
    ) -> None:
        await self.dispatch_after("nack", consumer, message, raw_message)
        await self._nack(raw_message, delay)
        await self.dispatch_after("nack", consumer, message, raw_message)

    async def connect(self) -> None:
        await self.dispatch_before("broker_connect")
        await self._connect()
        await self.dispatch_after("broker_connect")

    async def disconnect(self) -> None:
        await self.dispatch_before("broker_disconnect")
        await self._disconnect()
        await self.dispatch_after("broker_disconnect")

    async def publish(self, message: EventT, **kwargs) -> None:
        await self.dispatch_before("publish", message)
        await self._publish(message, **kwargs)
        await self.dispatch_after("publish", message)

    async def start_consumer(self, consumer: ConsumerT):
        await self.dispatch_before("consumer_start", consumer)
        await self._start_consumer(consumer)
        await self.dispatch_after("consumer_start", consumer)

    def add_middleware(self, middleware: Middleware) -> None:
        if not isinstance(middleware, Middleware):
            raise TypeError(f"Middleware expected, got {type(middleware)}")
        self.middlewares.append(middleware)

    async def _dispatch(self, full_event: str, *args, **kwargs) -> None:
        for m in self.middlewares:
            await getattr(m, full_event)(self, *args, **kwargs)
            # try:
            #     await getattr(m, full_event)(self, *args, **kwargs)
            # except Exception as e:
            #     self.logger.error(f"Unhandled middleware exception {e}")

    async def dispatch_before(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"before_{event}", *args, **kwargs)

    async def dispatch_after(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"after_{event}", *args, **kwargs)

    # broker specific implementations below

    @staticmethod
    @abstractmethod
    def get_message_data(message: MessageT) -> bytes:
        raise NotImplementedError

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
    async def _start_consumer(self, consumer: ConsumerT) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return broker connection status"""
        raise NotImplementedError

    @abstractmethod
    def get_num_delivered(self, raw_message: MessageT) -> int:
        raise NotImplementedError

    async def _ack(self, raw_message: MessageT) -> None:
        ...

    async def _nack(self, raw_message: MessageT, delay: int | None = None) -> None:
        ...
