from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gcloud.aio.pubsub import (
    PublisherClient,
    PubsubMessage,
    SubscriberClient,
    SubscriberMessage,
    subscribe,
)

from asvc.broker import Broker
from asvc.exceptions import BrokerError
from asvc.middleware import Middleware
from asvc.utils.functools import retry_async

if TYPE_CHECKING:
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent
    from asvc.types import Encoder


class PubSubBroker(Broker[SubscriberMessage]):
    def __init__(
        self,
        *,
        service_file: str,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.service_file = service_file
        self._client = None

    def parse_incoming_message(self, message: SubscriberMessage) -> Any:
        return self.encoder.decode(message.data)

    async def _disconnect(self) -> None:
        await self.client.close()

    async def _start_consumer(self, consumer: Consumer) -> None:
        consumer_client = SubscriberClient(service_file=self.service_file)
        handler = self.get_handler(consumer)
        await subscribe(
            subscription=consumer.topic,
            handler=handler,
            subscriber_client=consumer_client,
            **consumer.options.get("subscribe_options", {}),
        )

    @property
    def client(self) -> PublisherClient:
        if self._client is None:
            raise BrokerError("Broker not connected")
        return self._client

    @retry_async(max_retries=3)
    async def _publish(
        self,
        message: CloudEvent,
        timeout: int = 10,
        ordering_key: str | None = None,
        **kwargs,
    ) -> None:
        msg = PubsubMessage(
            data=self.encoder.encode(message.dict()),
            ordering_key=ordering_key or str(message.id),
        )
        await self.client.publish(topic=message.topic, messages=[msg], timeout=timeout)

    async def _connect(self) -> None:
        self._client = PublisherClient(service_file=self.service_file)

    @property
    def is_connected(self) -> bool:
        return self.client.session._session.closed
