from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable


from aio_services.consumer import Consumer
from aio_services.logger import get_logger

if TYPE_CHECKING:
    from aio_services.types import EventT, HandlerT, BrokerT


class Service:
    def __init__(
        self,
        name: str,
        broker: BrokerT,
    ):
        self.name = name
        self.broker = broker
        self.logger = get_logger(__name__, type(self))
        self.consumers: dict[str, Consumer] = {}
        self._tasks: list[asyncio.Task] = []

    def subscribe(
        self,
        topic: str,
        name: str | None = None,
        concurrency: int = 10,
        **options: Any,
    ) -> Callable[[HandlerT], HandlerT]:
        def wrapper(func: HandlerT) -> HandlerT:
            consumer: Consumer = Consumer(
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
        await self.broker.connect()
        for consumer in self.consumers.values():
            task = asyncio.create_task(self.broker.start_consumer(consumer))
            self._tasks.append(task)

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.broker.disconnect()

    def inject_to_starlette_app(self, app) -> None:
        app.on_event("startup")(self.start)
        app.on_event("shutdown")(self.stop)

    def inject_to_aiohttp_app(self, app) -> None:
        app.on_startup.append(self.start)
        app.on_shutdown.apeend(self.stop)
