from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic

import async_timeout
from pydantic import ValidationError

from aio_services import CloudEvent
from aio_services.exceptions import DecodeError, Reject, Skip
from aio_services.logger import LoggerMixin
from aio_services.middleware import Middleware
from aio_services.middlewares import default_middlewares
from aio_services.types import AbstractIncomingMessage, RawMessage, T

if TYPE_CHECKING:
    from aio_services.types import AbstractMessage, ConsumerP, Encoder


class AbstractBroker(ABC, Generic[RawMessage]):
    @abstractmethod
    def parse_incoming_message(self, message: RawMessage) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def _publish(self, message: AbstractMessage, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _start_consumer(self, consumer: ConsumerP) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return broker connection status"""
        raise NotImplementedError

    async def _ack(self, message: AbstractIncomingMessage[T, RawMessage]) -> None:
        """Empty default implementation for brokers that do not support explicit ack"""

    async def _nack(
        self, message: AbstractIncomingMessage[T, RawMessage], delay: int | None = None
    ) -> None:
        """Same as for ._ack()"""


class BaseBroker(AbstractBroker[RawMessage], LoggerMixin, ABC):
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
        self.middlewares = []

        if middlewares is None:
            middlewares = [m() for m in default_middlewares]

        for m in middlewares:
            self.add_middleware(m)

        self.options = options
        self._lock = asyncio.Lock()
        self._is_connected = False

    def __repr__(self):
        return type(self).__name__

    def get_handler(
        self, consumer: ConsumerP
    ) -> Callable[[RawMessage], Awaitable[None]]:
        async def handler(raw_message: RawMessage) -> None:
            exc = None
            result = None
            try:
                parsed = self.parse_incoming_message(raw_message)
                message = consumer.validate_message(parsed)
                setattr(message, "_raw", raw_message)

            except (DecodeError, ValidationError) as e:
                self.logger.exception(
                    "Parsing error Decode/Validation error", exc_info=e
                )
                return

            try:
                await self.dispatch_before("process_message", consumer, message)
            except Skip:
                self.logger.info(f"Skipped message {message.id}")
                await self.dispatch_after("skip_message", message)
                await self.ack(consumer, message)
                return
            try:
                async with async_timeout.timeout(consumer.timeout):
                    result = await consumer.process(message)

            # TODO: asyncio.CanceledError handling (?)
            except Reject as e:
                exc = e
                self.logger.error(f"Message {message.id} rejected. {e}")
            except Exception as e:
                exc = e
            finally:
                await self.dispatch_after("process_message", message, result, exc)
                if exc and isinstance(exc, Reject):
                    await self.nack(consumer, message)
                else:
                    await self.ack(consumer, message)

        return handler

    async def ack(
        self, consumer: ConsumerP, message: AbstractIncomingMessage[T, RawMessage]
    ) -> None:
        await self.dispatch_before("ack", consumer, message)
        await self._ack(message)
        await self.dispatch_after("ack", consumer, message)

    async def nack(
        self,
        consumer: ConsumerP,
        message: AbstractIncomingMessage[T, RawMessage],
        delay: int | None = None,
    ) -> None:
        await self.dispatch_after(
            "nack",
            consumer,
            message,
        )
        await self._nack(message, delay)
        await self.dispatch_after(
            "nack",
            consumer,
            message,
        )

    async def connect(self) -> None:
        async with self._lock:
            if not self._is_connected:
                await self.dispatch_before("broker_connect")
                await self._connect()
                self._is_connected = True
                await self.dispatch_after("broker_connect")

    async def disconnect(self) -> None:
        async with self._lock:
            if self._is_connected:
                await self.dispatch_before("broker_disconnect")
                await self._disconnect()
                self._is_connected = False
                await self.dispatch_after("broker_disconnect")

    async def publish_event(self, message: CloudEvent, **kwargs):
        await self.dispatch_before("publish", message)
        await self._publish(message, **kwargs)
        await self.dispatch_after("publish", message)

    async def publish(
        self,
        topic: str,
        type_: type[CloudEvent] | str,
        data: Any,
        source: str,
        **kwargs,
    ) -> None:

        cls: type[CloudEvent] = CloudEvent if isinstance(type_, str) else type_
        type_name = type_ if isinstance(type_, str) else type_.__name__

        message = cls(
            content_type=self.encoder.CONTENT_TYPE,
            topic=topic,
            type=type_name,
            data=data,
            source=source,
            **kwargs,
        )
        await self.publish_event(message)

    async def start_consumer(self, consumer: ConsumerP):
        await self.dispatch_before("consumer_start", consumer)
        await self._start_consumer(consumer)
        await self.dispatch_after("consumer_start", consumer)

    def add_middleware(self, middleware: Middleware) -> None:
        if not isinstance(middleware, Middleware):
            raise TypeError(f"Middleware expected, got {type(middleware)}")
        self.middlewares.append(middleware)

    async def _dispatch(self, full_event: str, *args, **kwargs) -> None:
        for m in self.middlewares:
            try:
                await getattr(m, full_event)(self, *args, **kwargs)
            except Skip:
                raise
            # TODO: uncomment after tests
            # except Exception as e:
            #     self.logger.error(f"Unhandled middleware exception {e}")

    async def dispatch_before(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"before_{event}", *args, **kwargs)

    async def dispatch_after(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"after_{event}", *args, **kwargs)
