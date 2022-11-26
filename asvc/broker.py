from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic

import async_timeout
from pydantic import ValidationError

from asvc import CloudEvent
from asvc.exceptions import DecodeError, Reject, Skip
from asvc.logger import LoggerMixin
from asvc.middleware import Middleware
from asvc.middlewares import default_middlewares
from asvc.types import Encoder, RawMessage

if TYPE_CHECKING:
    from asvc.consumer import Consumer


class AbstractBroker(ABC, Generic[RawMessage]):
    @abstractmethod
    def parse_incoming_message(self, message: RawMessage) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def _publish(self, message: CloudEvent, **kwargs) -> None:
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

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return broker connection status"""
        raise NotImplementedError

    async def _ack(self, message: CloudEvent) -> None:
        """Empty default implementation for backends that do not support explicit ack"""

    async def _nack(self, message: CloudEvent, delay: int | None = None) -> None:
        """Same as for ._ack()"""


class Broker(AbstractBroker[RawMessage], LoggerMixin, ABC):
    def __init__(
        self,
        *,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options,
    ) -> None:
        """Base broker class"""
        if encoder is None:
            from asvc.encoders import get_default_encoder

            encoder = get_default_encoder()

        self.encoder = encoder
        self.middlewares: list[Middleware] = []

        if middlewares is None:
            middlewares = [m() for m in default_middlewares]

        for m in middlewares:
            self.add_middleware(m)

        self.options = options
        self._lock = asyncio.Lock()
        self._stopped = True

    def __repr__(self):
        return type(self).__name__

    def get_handler(
        self, consumer: Consumer
    ) -> Callable[[RawMessage], Awaitable[Any | None]]:
        async def handler(raw_message: RawMessage) -> None:
            exc: Exception | None = None
            result: Any = None
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
                    self.logger.info(
                        f"Running consumer {consumer.name} with message {message.id}"
                    )
                    result = await consumer.process(message)
                if consumer.forward_response and result is not None:
                    await self.publish_event(
                        CloudEvent(
                            type=consumer.forward_response.as_type,
                            topic=consumer.forward_response.topic,
                            data=result,
                            trace_id=message.trace_id,
                            source=consumer.service_name,
                        )
                    )
            # TODO: asyncio.CanceledError handling (?)
            except Reject as e:
                exc = e
                self.logger.exception(f"Message {message.id} rejected", exc_info=e)
            except Exception as e:
                exc = e
            finally:
                await self.dispatch_after(
                    "process_message", consumer, message, result, exc
                )
                if exc and isinstance(exc, Reject):
                    await self.nack(consumer, message)
                else:
                    await self.ack(consumer, message)

        return handler

    async def ack(self, consumer: Consumer, message: CloudEvent) -> None:
        await self.dispatch_before("ack", consumer, message)
        await self._ack(message)
        await self.dispatch_after("ack", consumer, message)

    async def nack(
        self,
        consumer: Consumer,
        message: CloudEvent,
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
            if self._stopped:
                await self.dispatch_before("broker_connect")
                await self._connect()
                self._stopped = False
                await self.dispatch_after("broker_connect")

    async def disconnect(self) -> None:
        async with self._lock:
            if not self._stopped:
                await self.dispatch_before("broker_disconnect")
                self._stopped = True
                await self._disconnect()
                await self.dispatch_after("broker_disconnect")

    async def publish_event(self, message: CloudEvent, **kwargs):
        await self.dispatch_before("publish", message)
        await self._publish(message, **kwargs)
        await self.dispatch_after("publish", message)

    async def publish(
        self,
        topic: str,
        data: Any | None = None,
        type_: type[CloudEvent] | str = "CloudEvent",
        source: str = "",
        **kwargs,
    ) -> None:
        """Publish message to broker"""
        if isinstance(type_, str):
            cls = CloudEvent
            kwargs["type"] = type_
        else:
            cls = type_
        message: CloudEvent = cls(
            content_type=self.encoder.CONTENT_TYPE,
            topic=topic,
            data=data,
            source=source,
            **kwargs,
        )
        await self.publish_event(message)

    async def start_consumer(self, consumer: Consumer):
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
            except Exception as e:
                self.logger.exception("Unhandled middleware exception", exc_info=e)

    async def dispatch_before(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"before_{event}", *args, **kwargs)

    async def dispatch_after(self, event: str, *args, **kwargs) -> None:
        await self._dispatch(f"after_{event}", *args, **kwargs)

    @classmethod
    def from_env(cls, **kwargs):
        ...

    @classmethod
    def from_object(cls, obj, **kwargs):
        ...
