from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gcloud.aio.pubsub import (
    PublisherClient,
    PubsubMessage,
    SubscriberClient,
    SubscriberMessage,
    subscribe,
)

from aio_services.broker import Broker
from aio_services.middleware import Middleware
from aio_services.models import BaseConsumerOptions

if TYPE_CHECKING:
    from aio_services.types import ConsumerT, Encoder, EventT


class PubSubConsumerOptions(BaseConsumerOptions):
    ...


class PubSubBroker(Broker[PubSubConsumerOptions, SubscriberMessage]):
    ConsumerOptions = PubSubConsumerOptions

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

    @staticmethod
    def get_message_data(message: SubscriberMessage) -> bytes:
        return message.data

    async def _disconnect(self) -> None:
        await self.client.close()

    async def _start_consumer(self, consumer: ConsumerT) -> None:
        consumer_client = SubscriberClient(service_file=self.service_file)
        handler = self.get_handler(consumer)
        await subscribe(
            subscription=consumer.topic,
            handler=handler,
            subscriber_client=consumer_client,
            **consumer.options,
        )

    @property
    def client(self) -> PublisherClient:
        assert self._client, "Broker not connected"
        return self._client

    async def _publish(
        self,
        message: EventT,
        timeout: int = 10,
        ordering_key: str | None = None,
        **kwargs,
    ) -> None:
        msg = PubsubMessage(
            data=self.encoder.encode(message),
            ordering_key=ordering_key or str(message.id),
        )
        await self.client.publish(topic=message.topic, messages=[msg], timeout=timeout)

    async def _connect(self) -> None:
        self._client = PublisherClient(service_file=self.service_file)
