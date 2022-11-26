from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiokafka

from asvc.broker import Broker
from asvc.exceptions import BrokerError
from asvc.middleware import Middleware

if TYPE_CHECKING:
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent
    from asvc.types import Encoder


class KafkaBroker(Broker[aiokafka.ConsumerRecord]):
    def __init__(
        self,
        *,
        bootstrap_servers: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        publisher_options: dict[str, Any] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.bootstrap_servers = bootstrap_servers
        self._publisher_options = publisher_options or {}
        self._publisher = None

    def parse_incoming_message(self, message: aiokafka.ConsumerRecord) -> Any:
        return self.encoder.decode(message.value)

    @property
    def is_connected(self) -> bool:
        return True

    async def _start_consumer(self, consumer: Consumer):
        handler = self.get_handler(consumer)
        subscriber = aiokafka.AIOKafkaConsumer(
            consumer.topic,
            group_id=consumer.service_name,
            bootstrap_servers=self.bootstrap_servers,
            enable_auto_commit=False,
        )
        await subscriber.start()
        while self._stopped:
            result = await subscriber.getmany(
                timeout_ms=consumer.options.get("timeout_ms", 600)
            )
            for tp, messages in result.items():

                if messages:
                    tasks: list[asyncio.Task] = [
                        asyncio.create_task(handler(message)) for message in messages  # type: ignore
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    await subscriber.commit({tp: messages[-1].offset + 1})

    async def _disconnect(self):
        if self._publisher:
            await self._publisher.stop()

    @property
    def publisher(self) -> aiokafka.AIOKafkaProducer:
        if self._publisher is None:
            raise BrokerError("Broker not connected")
        return self._publisher

    async def _connect(self):
        self._publisher = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers, **self._publisher_options
        )
        await self._publisher.start()

    async def _publish(
        self,
        message: CloudEvent,
        key: Any | None = None,
        partition: Any | None = None,
        headers: dict[str, str] | None = None,
        timestamp_ms: int | None = None,
        **kwargs: Any,
    ):
        data = self.encoder.encode(message.dict())
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
