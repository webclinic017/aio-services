import asyncio
from dataclasses import dataclass
from typing import Type, Any, Dict

from aio_services.broker import Broker, Consumer, MessageProxy
from aio_services.types import DataT


@dataclass
class StubMessage:
    data: Any


class StubMessageProxy(MessageProxy[StubMessage, DataT]):
    pass


class StubConsumer(Consumer[StubMessage]):
    async def _consume(self, broker: "StubBroker") -> None:
        asyncio.create_task(self._consume_task(broker))

    async def _consume_task(self, broker):
        broker.topics.setdefault(self.topic, asyncio.Queue())
        queue = broker.topics[self.topic]
        while True:
            message = await queue.get()
            await self._process_message(broker, message)
            queue.task_done()


class StubBroker(Broker[StubMessage]):
    def __init__(self, *, group_id: str, **options):
        super().__init__(group_id=group_id, **options)
        self.topics: Dict[str, asyncio.Queue] = {}

    @property
    def consumer_class(self) -> Type[StubConsumer[StubMessage]]:
        return StubConsumer

    async def _publish(self, topic: str, message, **kwargs):
        topic = self.topics.get(topic)
        await topic.put(message)
