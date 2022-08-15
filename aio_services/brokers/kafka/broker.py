from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiokafka

from aio_services.broker import Broker
from aio_services.middleware import Middleware
from aio_services.models import BaseConsumerOptions

if TYPE_CHECKING:
    from aio_services.types import ConsumerT, Encoder, EventT


class KafkaConsumerOptions(BaseConsumerOptions):
    timeout_ms: int = 60


class KafkaBroker(Broker[KafkaConsumerOptions, aiokafka.ConsumerRecord]):
    ConsumerOptions = KafkaConsumerOptions

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.bootstrap_servers = bootstrap_servers
        self._publisher = None

    @staticmethod
    def get_message_data(message: aiokafka.ConsumerRecord) -> bytes:
        return message.value

    async def _start_consumer(self, consumer: ConsumerT):
        handler = self.get_handler(consumer)
        consumer_options = self.get_consumer_options(consumer)
        subscriber = aiokafka.AIOKafkaConsumer(
            consumer.topic,
            group_id=consumer.service_name,
            bootstrap_servers=self.bootstrap_servers,
            enable_auto_commit=False,
        )
        await subscriber.start()
        while True:
            result = await subscriber.getmany(timeout_ms=consumer_options.timeout_ms)
            for tp, messages in result.items():
                if messages:
                    tasks = [
                        asyncio.create_task(handler(message) for message in messages)
                    ]
                    await asyncio.gather(*tasks)
                    await subscriber.commit({tp: messages[-1].offset + 1})

    async def _disconnect(self):
        await self.publisher.stop()

    @property
    def publisher(self) -> aiokafka.AIOKafkaProducer:
        assert self._publisher is not None, "Broker not connected"
        return self._publisher

    async def _connect(self):
        publisher_options = self.options.get("publisher_options", {})
        self._publisher = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers, **publisher_options
        )
        await self._publisher.start()

    async def _publish(
        self,
        message: EventT,
        key: Any | None = None,
        partition: Any | None = None,
        headers: dict[str, str] | None = None,
        timestamp_ms: int | None = None,
        **kwargs: Any,
    ):
        data = self.encoder.encode(message)
        timestamp_ms = timestamp_ms or int(message.time.timestamp() * 1000)
        key = key or getattr(message, "key", None)
        await self.publisher.send(
            topic=message.topic,
            value=data,
            key=key,
            partition=partition,
            headers=headers,
            timestamp_ms=timestamp_ms,
        )
