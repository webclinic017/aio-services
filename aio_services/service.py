from __future__ import annotations

import asyncio
from typing import Any, cast

from aio_services import CloudEvent
from aio_services.consumer import Consumer, GenericConsumer
from aio_services.logger import LoggerMixin
from aio_services.types import BrokerT, ConsumerP, MessageHandlerT


class Service(LoggerMixin):
    def __init__(self, name: str, broker: BrokerT):
        self.name = name
        self.broker = broker
        self.consumers: dict[str, ConsumerP] = {}
        self._tasks: list[asyncio.Task] = []

    def subscribe(
        self,
        topic: str,
        name: str | None = None,
        concurrency: int = 10,
        **options: Any,
    ):
        def wrapper(func_or_cls: MessageHandlerT) -> MessageHandlerT:
            if callable(func_or_cls):
                consumer = Consumer(
                    service_name=self.name,
                    topic=topic,
                    fn=func_or_cls,
                    name=name or func_or_cls.__name__,
                    concurrency=concurrency,
                    **options,
                )
            elif issubclass(func_or_cls, GenericConsumer):
                consumer = func_or_cls(
                    service_name=self.name,
                    topic=topic,
                    name=name or func_or_cls.__name__,
                    concurrency=concurrency,
                    **options,
                )
            else:
                raise TypeError("Unknown handler")
            self.consumers[consumer.name] = cast(
                ConsumerP, consumer
            )  # this shouldn't be cast
            return func_or_cls

        return wrapper

    async def publish_event(self, message: CloudEvent, **kwargs: Any) -> None:
        await self.broker.publish_event(message, **kwargs)

    async def publish(self, topic: str, type_, data: Any, **kwargs):
        await self.broker.publish(topic, type_, data, source=self.name, **kwargs)

    async def start(self) -> None:
        await self.broker.connect()
        await self.broker.dispatch_before("service_start", self)
        self._tasks = [
            asyncio.create_task(self.broker.start_consumer(consumer))
            for consumer in self.consumers.values()
        ]
        await self.broker.dispatch_after("service_start", self)

    async def stop(self, *args, **kwargs) -> None:
        print(args, kwargs)
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        await self.broker.disconnect()


class ServiceGroup:
    # TODO: inherit from user list

    def __init__(self, services: list[Service] | None = None):
        self.services = services or []

    def add_service(self, service: Service):
        self.services.append(service)

    async def start(self) -> None:
        await asyncio.gather(*[svc.start() for svc in self.services])

    async def stop(self) -> None:
        await asyncio.gather(*[svc.stop() for svc in self.services])
