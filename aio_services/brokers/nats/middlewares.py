from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from nats.js.kv import KeyValue

from aio_services.brokers.nats.broker import JetStreamBroker
from aio_services.middleware import Middleware

if TYPE_CHECKING:
    from aio_services.types import AbstractIncomingMessage, ConsumerP, Encoder


class NatsJetStreamResultMiddleware(Middleware[JetStreamBroker]):
    def __init__(self, bucket: str, encoder: Encoder | None = None, **options: Any):
        self.bucket = bucket
        if encoder is None:
            from aio_services.encoders import get_default_encoder

            encoder = get_default_encoder()
        self.encoder = encoder
        self.options = options
        self._kv = None

    @property
    def kv(self) -> KeyValue:
        return self._kv

    async def get(self, key: str) -> Any:
        kv = await self.kv.get(key)
        return self.encoder.decode(kv.value)

    async def get_message_result(
        self, message_id: UUID, timeout: int = 10
    ) -> Any | None:
        # TODO: timeout
        return await self.get(str(message_id))

    async def after_broker_connect(self, broker: JetStreamBroker):
        self._kv = await broker.js.create_key_value(bucket=self.bucket, **self.options)

    async def after_process_message(
        self,
        broker: JetStreamBroker,
        consumer: ConsumerP,
        message: AbstractIncomingMessage,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """Store message result in JetStream K/V Store"""
        if exc is None and "store_results" in consumer.options:
            data = self.encoder.encode(result)
            await self.kv.put(str(message.id), data)
