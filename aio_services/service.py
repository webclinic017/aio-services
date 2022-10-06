from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable

from aio_services.consumer import Consumer
from aio_services.logger import LoggerMixin

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, EventT, HandlerT


class Service(LoggerMixin):
    def __init__(self, name: str, broker: BrokerT, auto_connect: bool = True):
        self.name = name
        self.broker = broker
        self.auto_connect = auto_connect
        self.consumers: dict[str, Consumer] = {}
        self._tasks: list[asyncio.Task] = []

    def subscribe(
        self,
        topic: str,
        name: str | None = None,
        concurrency: int = 10,
        consumer_class: type[ConsumerT] = Consumer,
        **options: Any,
    ) -> Callable[[HandlerT], HandlerT]:
        def wrapper(func: HandlerT) -> HandlerT:
            consumer: Consumer = consumer_class(
                service_name=self.name,
                topic=topic,
                fn=func,
                name=name,
                concurrency=concurrency,
                **options,
            )
            self.consumers[consumer.name] = consumer
            return func

        return wrapper

    async def publish(self, message: EventT, **kwargs: Any) -> None:
        message.source = self.name
        await self.broker.publish(message, **kwargs)

    async def start(self) -> None:
        if self.auto_connect:
            await self.broker.connect()
        await self.broker.dispatch_before("service_start", self)
        self._tasks = [
            asyncio.create_task(self.broker.start_consumer(consumer))
            for consumer in self.consumers.values()
        ]
        await self.broker.dispatch_after("service_start", self)

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        if self.auto_connect:
            await self.broker.disconnect()
