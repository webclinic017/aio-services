from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aio_pika

from aio_services.broker import Broker
from aio_services.middleware import Middleware
from aio_services.models import BaseConsumerOptions, CloudCommand

if TYPE_CHECKING:
    from aio_services.types import ConsumerT, Encoder, EventT


class RabbitmqConsumerOptions(BaseConsumerOptions):
    prefetch_count: int = 10
    queue_options: dict[str, Any] = {}


class RabbitmqBroker(
    Broker[RabbitmqConsumerOptions, aio_pika.abc.AbstractIncomingMessage]
):
    ConsumerOptions = RabbitmqConsumerOptions

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
        self._connection = None
        self.queues: dict[str, aio_pika.abc.AbstractRobustQueue] = {}
        self._events_exchange = None
        self._commands_exchange = None

    @staticmethod
    def get_message_data(message: aio_pika.IncomingMessage) -> bytes:
        return message.body

    async def _disconnect(self) -> None:
        await self.connection.close()

    async def _start_consumer(self, consumer: ConsumerT) -> None:
        channel = await self.connection.channel()
        options: RabbitmqConsumerOptions = self.get_consumer_options(consumer)
        await channel.set_qos(prefetch_count=options.prefetch_count)
        queue = await channel.declare_queue(consumer.topic, **options.queue_options)
        if issubclass(consumer.event_type, CloudCommand):
            exchange = self._commands_exchange
        else:
            exchange = self._events_exchange
        await queue.bind(exchange, routing_key=consumer.topic)
        self.queues[consumer.name] = queue
        handler = self.get_handler(consumer)
        await queue.consume(handler)
        try:
            # Wait until terminate ?
            await asyncio.Future()
        finally:
            await channel.close()

    @property
    def connection(self) -> aio_pika.RobustConnection:
        return self._connection

    async def _connect(self) -> None:
        _connection = await aio_pika.connect_robust(self.url, **self.options)
        self._connection = _connection
        channel = await _connection.channel()
        self._events_exchange = channel.declare_exchange(
            name="events", type=aio_pika.ExchangeType.TOPIC, durable=True, passive=True
        )
        self._commands_exchange = channel.declare_exchange(
            name="commands",
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
            passive=True,
        )

    async def _publish(self, message: EventT, **kwargs) -> None:
        body = self.encoder.encode(message)
        msg = aio_pika.Message(
            body=body,
            app_id=message.source,
            content_type=message.content_type,
            timestamp=message.time,
            message_id=str(message.id),
            type=message.type,
            content_encoding="UTF-8",
        )
        # channel = await self.connection.channel()
        if issubclass(message, CloudCommand):
            exchange: aio_pika.Exchange = self._commands_exchange
        else:
            exchange = self._events_exchange

        await exchange.publish(msg, routing_key=message.topic, **kwargs)
