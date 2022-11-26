from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from asvc.broker import Broker
from asvc.middleware import Middleware

if TYPE_CHECKING:
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent
    from asvc.types import Encoder


@dataclass
class Message:
    data: bytes
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

    def parse_incoming_message(self, message: Message) -> Any:
        return self.encoder.decode(message.data)

    async def _disconnect(self) -> None:
        self._stopped = True

    async def _start_consumer(self, consumer: Consumer):
        queue = self.topics[consumer.topic]
        handler = self.get_handler(consumer)
        while not self._stopped:
            message = await queue.get()
            await handler(message)

    async def _connect(self) -> None:
        pass

    async def _publish(self, message: CloudEvent, **_) -> None:
        queue = self.topics[message.topic]
        data = self.encoder.encode(message.dict())
        msg = Message(data=data, queue=queue)
        await queue.put(msg)

    async def _ack(self, message: CloudEvent) -> None:
        message.raw.queue.task_done()

    async def _nack(self, message: CloudEvent, delay: int | None = None) -> None:

        if delay:
            await asyncio.sleep(delay)
        await message.raw.queue.put(message.raw)

    def is_connected(self) -> bool:
        return True
