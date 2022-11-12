from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aio_services.broker import BaseBroker
from aio_services.middleware import Middleware

if TYPE_CHECKING:
    from aio_services.types import (
        AbstractIncomingMessage,
        AbstractMessage,
        ConsumerP,
        Encoder,
        T,
    )


@dataclass
class Message:
    data: bytes
    queue: asyncio.Queue | None = None


class StubBroker(BaseBroker[Message]):
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

    async def _start_consumer(self, consumer: ConsumerP):
        queue = self.topics[consumer.topic]
        handler = self.get_handler(consumer)
        while not self._stopped:
            message = await queue.get()
            await handler(message)

    async def _connect(self) -> None:
        pass

    async def _publish(self, message: AbstractMessage, **_) -> None:
        queue = self.topics[message.topic]
        data = self.encoder.encode(message.dict())
        msg = Message(data=data, queue=queue)
        await queue.put(msg)

    async def _ack(self, message: AbstractIncomingMessage[T, Message]) -> None:
        message.raw.queue.task_done()

    async def _nack(
        self, message: AbstractIncomingMessage[T, Message], delay: int | None = None
    ) -> None:

        if delay:
            await asyncio.sleep(delay)
        await message.raw.queue.put(message.raw)

    def is_connected(self) -> bool:
        return True
