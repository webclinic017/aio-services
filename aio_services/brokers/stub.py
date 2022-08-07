from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from aio_services.broker import Broker
from aio_services.middleware import Middleware
from aio_services.models import BaseConsumerOptions

if TYPE_CHECKING:
    from aio_services.consumer import Consumer
    from aio_services.types import EventT, Encoder


class StubBroker(Broker[BaseConsumerOptions, bytes]):
    ConsumerOptions = BaseConsumerOptions

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
    def get_message_data(message: bytes) -> bytes:
        return message

    async def _disconnect(self) -> None:
        self._stopped = True

    async def _start_consumer(self, consumer: Consumer):
        queue = self.topics[consumer.topic]
        handler = self.get_handler(consumer)
        while not self._stopped:
            message = await queue.get()
            await handler(message)
            queue.task_done()

    async def _connect(self) -> None:
        ...

    async def _publish(self, message: EventT, **kwargs) -> None:
        topic = self.topics[message.topic]
        data = self.encoder.encode(message)
        await topic.put(data)
