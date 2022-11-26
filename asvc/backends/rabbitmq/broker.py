from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aio_pika

from asvc.broker import Broker
from asvc.middleware import Middleware

if TYPE_CHECKING:
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent
    from asvc.types import Encoder


class RabbitmqBroker(Broker[aio_pika.abc.AbstractIncomingMessage]):
    def __init__(
        self,
        *,
        url: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        prefetch_count: int = 10,
        queue_options: dict[str, Any] = None,
        exchange_name: str = "events",
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.url = url
        self.prefetch_count = prefetch_count
        self.queue_options = queue_options or {}
        self.exchange_name = exchange_name
        self._connection = None
        self._exchange = None
        self._channels: list[aio_pika.abc.AbstractRobustChannel] = []

    async def _disconnect(self) -> None:
        await asyncio.gather(
            *[c.close() for c in self._channels], return_exceptions=True
        )
        await self.connection.close()

    async def _start_consumer(self, consumer: Consumer) -> None:
        channel = await self.connection.channel()
        await channel.set_qos(
            prefetch_count=consumer.options.get("prefetch_count", self.prefetch_count)
        )
        options: dict[str, Any] = consumer.options.get(
            "queue_options", self.queue_options
        )
        is_durable = not consumer.dynamic
        options.setdefault("durable", is_durable)
        queue = await channel.declare_queue(name=consumer.full_name, **options)
        await queue.bind(self._exchange, routing_key=consumer.topic)
        handler = self.get_handler(consumer)
        await queue.consume(handler)
        self._channels.append(channel)

    @property
    def connection(self) -> aio_pika.RobustConnection:
        return self._connection

    @property
    def exchange(self) -> aio_pika.abc.AbstractRobustExchange:
        return self._exchange

    async def _connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self.url, **self.options)
        channel = await self.connection.channel()
        self._exchange = await channel.declare_exchange(
            name=self.exchange_name, type=aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def _publish(self, message: CloudEvent, **kwargs) -> None:
        body = self.encoder.encode(message.data)
        headers = kwargs.pop("headers", {})
        headers.setdefault("X-Trace-ID", str(message.trace_id))
        headers.setdefault("version", "1.0")
        msg = aio_pika.Message(
            headers=headers,
            body=body,
            app_id=message.source,
            content_type=message.content_type,
            timestamp=message.time,
            message_id=str(message.id),
            type=message.type,
            content_encoding="UTF-8",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(msg, routing_key=message.topic, **kwargs)

    async def _ack(self, message: CloudEvent) -> None:
        await message.raw.ack()

    async def _nack(self, message: CloudEvent, delay: int | None = None) -> None:
        # TODO: add delay support via rabbitmq delayed messages plugin
        await message.raw.reject(requeue=True)

    @property
    def is_connected(self) -> bool:
        return not self.connection.is_closed

    def parse_incoming_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> Any:
        return dict(
            id=message.message_id,
            trace_id=message.headers.get("X-Trace-ID"),
            type=message.type,
            data=self.encoder.decode(message.body),
            source=message.app_id,
            content_type=message.content_type,
            version=message.headers.get("version", "1.0"),
            time=message.timestamp,
            topic=message.routing_key,
        )
