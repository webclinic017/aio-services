from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from nats.js.errors import KeyNotFoundError
from nats.js.kv import KeyValue

from asvc.backends.nats.broker import JetStreamBroker
from asvc.middleware import Middleware
from asvc.utils.functools import retry_async

if TYPE_CHECKING:
    from asvc.broker import Broker
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent
    from asvc.types import Encoder


class NatsJetStreamResultMiddleware(Middleware):
    def __init__(self, bucket: str, encoder: Encoder | None = None, **options: Any):
        self.bucket = bucket
        if encoder is None:
            from asvc.encoders import get_default_encoder

            encoder = get_default_encoder()
        self.encoder = encoder
        self.options = options
        self._kv = None

    @property
    def kv(self) -> KeyValue:
        return self._kv

    @retry_async(max_retries=3, backoff=5)
    async def get(self, key: str) -> Any | None:
        kv = await self.kv.get(key)
        return self.encoder.decode(kv.value)

    async def get_or_none(self, key: str):
        try:
            return await self.get(key)
        except KeyNotFoundError:
            self.logger.warning(f"Key {key} not found")
            return None

    async def get_message_result(
        self, consumer_name: str, message_id: UUID
    ) -> Any | None:
        # TODO: timeout
        return await self.get(f"{consumer_name}:{message_id}")

    async def after_broker_connect(self, broker: Broker) -> None:
        assert isinstance(broker, JetStreamBroker)
        self._kv = await broker.js.create_key_value(bucket=self.bucket, **self.options)

    @retry_async(max_retries=3, backoff=10)
    async def after_process_message(
        self,
        broker: JetStreamBroker,
        consumer: Consumer,
        message: CloudEvent,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """Store message result in JetStream K/V Store"""
        if exc is None and "store_results" in consumer.options:
            data = self.encoder.encode(result)
            await self.kv.put(f"{consumer.name}:{message.id}", data)
