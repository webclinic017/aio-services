from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import nats
from nats.aio.msg import Msg as NatsMsg
from nats.js import JetStreamContext

from asvc.broker import Broker
from asvc.exceptions import BrokerError
from asvc.utils.functools import retry_async

if TYPE_CHECKING:
    from asvc.consumer import Consumer
    from asvc.middleware import Middleware
    from asvc.models import CloudEvent
    from asvc.types import Encoder


class NatsBroker(Broker[NatsMsg]):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        connection_options: dict[str, Any] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.url = url
        self.connection_options = connection_options or {}
        self._nc = None

    @property
    def nc(self) -> nats.NATS:
        if self._nc is None:
            raise BrokerError("Broker not connected. Call await broker.connect() first")
        return self._nc

    def parse_incoming_message(self, message: NatsMsg) -> Any:
        return self.encoder.decode(message.data)

    async def _start_consumer(self, consumer: Consumer) -> None:

        await self.nc.subscribe(
            subject=consumer.topic,
            queue=consumer.service_name,
            cb=self.get_handler(consumer),
        )

    async def _disconnect(self) -> None:
        if self._nc is not None:
            await self._nc.close()

    async def _connect(self) -> None:
        self._nc = await nats.connect(self.url, **self.connection_options)

    @retry_async(max_retries=3)
    async def _publish(self, message: CloudEvent, **kwargs) -> None:
        data = self.encoder.encode(message.dict())
        await self.nc.publish(message.topic, data, **kwargs)

    @property
    def is_connected(self) -> bool:
        return self.nc.is_connected


class JetStreamBroker(NatsBroker):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        prefetch_count: int = 10,
        fetch_timeout: int = 10,
        **options: Any,
    ) -> None:
        super().__init__(url=url, encoder=encoder, middlewares=middlewares, **options)
        self.prefetch_count = prefetch_count
        self.fetch_timeout = fetch_timeout
        self._js = None

    @property
    def js(self) -> JetStreamContext:
        if not (self._nc and self._js):
            raise BrokerError("Broker not connected")
        return self._js

    async def _connect(self) -> None:
        await super()._connect()
        self._js = self.nc.jetstream(**self.options.get("js_options", {}))

    @retry_async(max_retries=3)
    async def _publish(
        self,
        message: CloudEvent,
        timeout: float | None = None,
        stream: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        data = self.encoder.encode(message)
        await self.js.publish(
            subject=message.topic,
            payload=data,
            timeout=timeout,
            stream=stream,
            headers=headers,
        )

    async def _start_consumer(self, consumer: Consumer) -> None:
        subscription = await self.js.pull_subscribe(
            subject=consumer.topic,
            durable=consumer.full_name,
            config=consumer.options.get("config"),
        )
        handler = self.get_handler(consumer)
        try:
            while not self._stopped:
                try:
                    messages = await subscription.fetch(
                        batch=consumer.options.get(
                            "prefetch_count", self.prefetch_count
                        ),
                        timeout=consumer.options.get(
                            "fetch_timeout", self.fetch_timeout
                        ),
                    )
                    tasks = [asyncio.create_task(handler(message)) for message in messages]  # type: ignore
                    await asyncio.gather(*tasks, return_exceptions=True)
                except nats.errors.TimeoutError:
                    await asyncio.sleep(1)
        except Exception:
            self.logger.exception("Cancelling consumer")
        finally:
            if consumer.dynamic:
                await subscription.unsubscribe()

    async def _ack(self, message: CloudEvent) -> None:
        if not message.raw._ackd:
            await message.raw.ack()

    async def _nack(self, message: CloudEvent, delay=None) -> None:
        if not message.raw._ackd:
            await message.raw.nak(delay=delay)
