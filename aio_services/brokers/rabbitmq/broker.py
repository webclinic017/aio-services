from __future__ import annotations

from typing import TYPE_CHECKING, Any

import aio_pika

from aio_services.broker import Broker
from aio_services.middleware import Middleware
from aio_services.models import BaseConsumerOptions
from aio_services.types import Encoder, EventT

if TYPE_CHECKING:
    from aio_services.consumer import Consumer


class RabbitmqConsumerOptions(BaseConsumerOptions):
    prefetch_count: int = 10


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

    @staticmethod
    def get_message_data(message: aio_pika.IncomingMessage) -> bytes:
        return message.body

    async def _disconnect(self) -> None:
        await self.connection.close()

    async def _start_consumer(self, consumer: Consumer) -> None:
        channel = await self.connection.channel()
        options: RabbitmqConsumerOptions = self.get_consumer_options(consumer)
        await channel.set_qos(prefetch_count=options.prefetch_count)
        queue = await channel.declare_queue(
            consumer.topic, **self.options.get("queue_options", {})
        )
        self.queues[consumer.name] = queue
        handler = self.get_handler(consumer)
        await queue.consume(handler)

    @property
    def connection(self) -> aio_pika.RobustConnection:
        return self._connection

    async def _connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self.url, **self.options)

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
        channel = await self.connection.channel()
        try:
            await channel.default_exchange.publish(
                msg, routing_key=message.topic, timeout=10
            )
        finally:
            await channel.close()
