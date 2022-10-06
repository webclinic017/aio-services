from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aio_services.broker import Broker
from aio_services.middleware import Middleware

if TYPE_CHECKING:
    from aio_services.types import ConsumerT, Encoder, EventT


@dataclass
class Message:
    data: bytes
    num_delivered: int = 1
    queue: asyncio.Queue | None = None


class StubBroker(Broker[Message]):
    def __init__(
        self,
        *,
        encoder: Encoder | None = None,
        middlewares: list[Middleware] | None = None,
        **options: Any,
    ) -> None:
        super().__init__(encoder=encoder, middlewares=middlewares, **options)
        self.topics: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._stopped = False

    @staticmethod
    def get_message_data(message: Message) -> bytes:
        return message.data

    async def _disconnect(self) -> None:
        self._stopped = True

    async def _start_consumer(self, consumer: ConsumerT):
        queue = self.topics[consumer.topic]
        handler = self.get_handler(consumer)
        while not self._stopped:
            message = await queue.get()
            await handler(message)

    async def _connect(self) -> None:
        pass

    def get_num_delivered(self, raw_message: Message) -> int:
        return raw_message.num_delivered

    async def _publish(self, message: EventT, **_) -> None:
        topic = self.topics[message.topic]
        data = self.encoder.encode(message.dict())
        msg = Message(data=data, queue=topic)
        await topic.put(msg)

    async def _ack(self, raw_message: Message) -> None:
        raw_message.queue.task_done()

    async def _nack(self, raw_message: Message, delay: int | None = None) -> None:
        raw_message.num_delivered += 1
        if delay:
            await asyncio.sleep(delay)
        await raw_message.queue.put(raw_message)

    def is_connected(self) -> bool:
        return True
