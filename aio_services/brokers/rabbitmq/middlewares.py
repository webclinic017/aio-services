from __future__ import annotations

from typing import TYPE_CHECKING

from aio_pika import ExchangeType

from aio_services.brokers.rabbitmq.broker import RabbitmqBroker
from aio_services.middleware import Middleware
from aio_services.types import COpts

if TYPE_CHECKING:
    from aio_services.types import ConsumerT


class DeadLetterQueueMiddleware(Middleware[COpts, RabbitmqBroker]):
    def __init__(self, dlx_name: str = "dlx"):
        self.dlx_name = dlx_name
        self._dlx_exchange = None

    async def after_broker_connect(self, broker: RabbitmqBroker):
        channel = await broker.connection.channel()
        self._dlx_exchange = await channel.declare_exchange(
            name=self.dlx_name, type=ExchangeType.HEADERS, auto_delete=True
        )

    async def after_consumer_start(self, broker: RabbitmqBroker, consumer: ConsumerT):
        await broker.queues[consumer.name].bind(
            self._dlx_exchange, "", arguments={"From": consumer.topic, "x-match": "any"}
        )
