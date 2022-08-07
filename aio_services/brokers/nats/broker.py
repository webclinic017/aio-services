from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import nats
from nats.aio.msg import Msg as NatsMsg
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig

from aio_services.broker import Broker
from aio_services.exceptions import BrokerError
from aio_services.models import BaseConsumerOptions
from aio_services.utils.asyncio import backoff

if TYPE_CHECKING:
    from aio_services.consumer import Consumer
    from aio_services.middleware import Middleware
    from aio_services.types import Encoder, EventT


class NatsConsumerOptions(BaseConsumerOptions):
    max_msgs: int | None = None
    pending_msgs_limit: int | None = None
    pending_bytes_limit: int | None = None
    prefetch_count: int = 10
    timeout: int = 60
    config: ConsumerConfig | None = None


class NatsBroker(Broker[NatsConsumerOptions, NatsMsg]):
    ConsumerOptions = NatsConsumerOptions

    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.url = url
        self._nc = None

    @property
    def nc(self) -> nats.NATS:
        if self._nc is None:
            raise BrokerError("Broker not connected")
        return self._nc

    @staticmethod
    def get_message_data(message: NatsMsg) -> bytes:
        return message.data

    async def _start_consumer(self, consumer: Consumer) -> None:

        await self.nc.subscribe(
            subject=consumer.topic,
            queue=consumer.service_name,
            cb=self.get_handler(consumer),
            **self.get_consumer_options(consumer).dict(
                exclude={"prefetch_count", "timeout"}
            ),
        )

    async def _disconnect(self) -> None:
        if self._nc:
            await self._nc.close()

    async def _connect(self) -> None:
        self._nc = await nats.connect(self.url, **self.options.get("nc_options", {}))

    async def _publish(self, message: EventT, **kwargs) -> None:
        data = self.encoder.encode(message)
        await self.nc.publish(message.topic, data, **kwargs)

    async def _ack(self, message: NatsMsg) -> None:
        if not message._ackd:
            await message.ack()


class JetStreamBroker(NatsBroker):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(url=url, encoder=encoder, middlewares=middlewares, **options)
        self._js = None

    @property
    def js(self) -> JetStreamContext:
        if not (self._nc and self._js):
            raise BrokerError("Broker not connected")
        return self._js

    async def _connect(self) -> None:
        await super()._connect()
        self._js = self.nc.jetstream(**self.options.get("js_options", {}))

    @backoff(max_retries=3)
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

    async def _start_consumer(self, consumer: Consumer) -> None:
        options = self.get_consumer_options(consumer)
        subscription = await self.js.pull_subscribe(
            subject=consumer.topic, durable=consumer.service_name, config=options.config
        )
        handler = self.get_handler(consumer)
        while True:
            try:
                messages = await subscription.fetch(
                    batch=options.prefetch_count, timeout=options.timeout
                )
                tasks = [asyncio.create_task(handler(message) for message in messages)]
                await asyncio.gather(*tasks)
            except nats.errors.TimeoutError:
                pass
