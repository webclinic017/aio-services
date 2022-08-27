from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from nats.aio.msg import Msg as NatsMsg
from nats.js.api import StreamConfig
from nats.js.kv import KeyValue

from aio_services.brokers.nats.broker import JetStreamBroker, NatsBroker
from aio_services.brokers.nats.models import (
    RetryConsumerOptions,
    JetStreamResultConsumerOptions,
)
from aio_services.exceptions import Retry
from aio_services.middleware import Middleware
from aio_services.utils.functools import compute_backoff
from aio_services.types import COpts

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, Encoder, EventT, MessageT


class NatsRetryMessageMiddleware(Middleware[RetryConsumerOptions, NatsBroker]):
    ConsumerOptions = RetryConsumerOptions

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: NatsMsg,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """Retry message for nats broker"""
        if exc is None:
            return
        options = self.get_consumer_options(consumer)
        if options.throws and isinstance(exc, options.throws):
            return

        retries_so_far = raw_message.metadata.num_delivered
        retry_when = options.retry_when
        if (
            callable(retry_when)
            and not await retry_when(retries_so_far, exc)
            or retry_when is None
            and options.max_retries is not None
            and retries_so_far >= options.max_retries
        ):
            self.logger.error(f"Retry limit exceeded for message {message.id}.")
            return
        if isinstance(exc, Retry) and exc.delay is not None:
            delay = exc.delay
        else:
            _, delay = compute_backoff(
                retries_so_far,
                factor=options.min_backoff,
                max_backoff=options.max_backoff,
            )

        self.logger.info("Retrying message %r in %d milliseconds.", message.id, delay)
        await raw_message.nak(delay=delay)


class NatsJetStreamResultMiddleware(
    Middleware[JetStreamResultConsumerOptions, JetStreamBroker]
):
    ConsumerOptions = JetStreamResultConsumerOptions

    def __init__(self, bucket: str, encoder: Encoder | None = None, **params: Any):
        self.bucket = bucket
        if encoder is None:
            from aio_services.encoders import get_default_encoder

            encoder = get_default_encoder()
        self.encoder = encoder
        self.params = params
        self._kv = None

    @property
    def kv(self) -> KeyValue:
        return self._kv

    async def get(self, key: str) -> Any:
        kv = await self.kv.get(key)
        kv.value = self.encoder.decode(kv.value)
        return kv

    async def get_message_result(
        self, message_id: UUID, timeout: int = 10
    ) -> Any | None:
        # TODO: timeout
        return await self.get(str(message_id))

    async def after_broker_connect(self, broker: JetStreamBroker):
        self._kv = await broker.js.create_key_value(bucket=self.bucket, **self.params)

    async def after_process_message(
        self,
        broker: JetStreamBroker,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """Store message result in JetStream K/V Store"""
        if exc is None:
            opt = self.get_consumer_options(consumer)
            if opt.store_results:
                value = self.encoder.encode(result)
                await self.kv.put(str(message.id), value)


class JetStreamManagerMiddleware(Middleware[COpts, JetStreamBroker]):
    """Auto create streams for topics"""

    def __init__(self, streams_config: list[StreamConfig]):
        self.streams_config = streams_config

    async def after_broker_connect(self, broker: JetStreamBroker):
        for stream_config in self.streams_config:
            try:
                await broker.js.update_stream(stream_config)
            except Exception as e:
                self.logger.warning("Error during stream initialization", exc_info=e)
