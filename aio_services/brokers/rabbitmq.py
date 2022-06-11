import functools
from typing import Type

import aio_pika
from aio_pika import IncomingMessage
from aio_services.broker import Broker, Consumer, MessageProxy
from aio_services.types import DataT


class RabbitMessageProxy(MessageProxy[IncomingMessage, DataT]):
    async def _ack(self, **kwargs):
        await self._message.ack()

    async def _nack(self, *, multiple: bool = False, requeue: bool = True, **kwargs):
        await self._message.nack(multiple=multiple, requeue=requeue)


class RabbitmqConsumer(Consumer[IncomingMessage]):
    async def _consume(self, broker) -> None:
        channel = await broker.connection.channel()

        # Will take no more than 10 messages in advance
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(self.topic, **self.options)
        await queue.consume(functools.partial(self._process_message, broker))


class RabbitmqBroker(Broker[IncomingMessage]):
    def __init__(self, *, group_id: str, url: str, **options):
        super().__init__(group_id=group_id, **options)
        self.url = url
        self._connection = None

    @property
    def connection(self) -> aio_pika.RobustConnection:
        return self._connection

    async def connect(self):
        self._connection = await aio_pika.connect_robust(self.url, **self.options)

    async def _publish(self, topic: str, message, **kwargs):
        pass

    @property
    def consumer_class(self) -> Type[Consumer[IncomingMessage]]:
        return RabbitmqConsumer
