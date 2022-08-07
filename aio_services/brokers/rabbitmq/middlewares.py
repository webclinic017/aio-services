from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aio_pika import ExchangeType

from aio_services.brokers.rabbitmq.broker import RabbitmqBroker
from aio_services.middleware import Middleware

if TYPE_CHECKING:
    from aio_services.broker import Broker
    from aio_services.consumer import Consumer
    from aio_services.types import EventT, MessageT


class DeadLetterQueueMiddleware(Middleware):
    def __init__(self, dlx_name: str = "dlx"):
        self.dlx_name = dlx_name
        self._dlx_exchange = None

    @property
    def supported_brokers(self) -> type[Broker] | tuple[type[Broker]]:
        return RabbitmqBroker

    async def after_process_message(
        self,
        broker: Broker,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """TODO: nack?"""

    async def after_broker_connect(self, broker: RabbitmqBroker):
        channel = broker.connection.channel()
        self._dlx_exchange = await channel.declare_exchange(
            name=self.dlx_name, type=ExchangeType.HEADERS, auto_delete=True
        )

    async def after_consumer_start(self, broker: RabbitmqBroker, consumer: Consumer):
        await broker.queues[consumer.name].bind(
            self._dlx_exchange, "", arguments={"From": consumer.topic, "x-match": "any"}
        )
