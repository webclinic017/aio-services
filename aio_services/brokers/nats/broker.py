from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import nats
from nats.aio.msg import Msg as NatsMsg
from nats.js import JetStreamContext

from aio_services.broker import Broker
from aio_services.exceptions import BrokerError
from aio_services.utils.asyncio import retry_async

if TYPE_CHECKING:
    from aio_services.middleware import Middleware
    from aio_services.types import ConsumerT, Encoder, EventT


class NatsBroker(Broker[NatsMsg]):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: Middleware | None = None,
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

    @staticmethod
    def get_message_data(message: NatsMsg) -> bytes:
        return message.data

    async def _start_consumer(self, consumer: ConsumerT) -> None:

        await self.nc.subscribe(
            subject=consumer.topic,
            queue=consumer.service_name,
            cb=self.get_handler(consumer),
        )

    async def _disconnect(self) -> None:
        if self._nc:
            await self._nc.close()

    async def _connect(self) -> None:
        self._nc = await nats.connect(self.url, **self.connection_options)

    @retry_async(max_retries=3)
    async def _publish(self, message: EventT, **kwargs) -> None:
        data = self.encoder.encode(message.dict())
        await self.nc.publish(message.topic, data, **kwargs)

    @property
    def is_connected(self) -> bool:
        return self.nc.is_connected

    def get_num_delivered(self, raw_message: NatsMsg) -> int:
        return raw_message.metadata.num_delivered


class JetStreamBroker(NatsBroker):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: Middleware | None = None,
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
        message: EventT,
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

    async def _start_consumer(self, consumer: ConsumerT) -> None:
        subscription = await self.js.pull_subscribe(
            subject=consumer.topic,
            durable=consumer.service_name,
            config=consumer.options.get("config"),
        )
        handler = self.get_handler(consumer)
        while True:
            try:
                messages = await subscription.fetch(
                    batch=consumer.options.get("prefetch_count", self.prefetch_count),
                    timeout=consumer.options.get("fetch_timeout", self.fetch_timeout),
                )
                tasks = [asyncio.create_task(handler(message)) for message in messages]  # type: ignore
                await asyncio.gather(*tasks, return_exceptions=True)
            except nats.errors.TimeoutError:
                await asyncio.sleep(0)

    async def _ack(self, raw_message: NatsMsg) -> None:
        if not raw_message._ackd:
            await raw_message.ack()

    async def _nack(self, raw_message: NatsMsg, delay=None) -> None:
        if not raw_message._ackd:
            await raw_message.nak(delay=delay)
