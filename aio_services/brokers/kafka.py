from typing import Type

import aiokafka
from aio_services.broker import AbstractConsumer, AbstractBroker


class KafkaConsumer(AbstractConsumer):
    async def _consume(self, broker: "KafkaBroker") -> None:
        subscriber = aiokafka.AIOKafkaConsumer(
            self.topic,
            group_id=self.group_id,
            bootstrap_servers=broker.bootstrap_servers,
            **self.options
        )
        await subscriber.start()

        async for message in subscriber:
            await self._process_message(message)

    async def _process_message(self, message):
        pass


class KafkaBroker(AbstractBroker):
    def __init__(self, *, group_id: str, bootstrap_servers: str, producer_options=None):
        super().__init__(group_id=group_id)
        self.bootstrap_servers = bootstrap_servers
        self.producer_options = producer_options or {}
        self._producer = None

    @property
    def producer(self) -> aiokafka.AIOKafkaProducer:
        assert self._producer is not None, "Broker not connected"
        return self._producer

    async def connect(self):
        self._producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers, **self.producer_options
        )
        await self.producer.start()

    async def _publish(self, topic: str, message, **kwargs):
        data = self.encoder.encode(message)
        await self.producer.send(topic=topic, value=data, **kwargs)

    @property
    def consumer_class(self) -> Type[AbstractConsumer]:
        return KafkaConsumer
