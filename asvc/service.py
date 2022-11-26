from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from asvc import CloudEvent
from asvc.consumer import Consumer, GenericConsumer
from asvc.logger import LoggerMixin

if TYPE_CHECKING:
    from asvc.broker import Broker
    from asvc.types import MessageHandlerT


class Service(LoggerMixin):
    def __init__(self, name: str, broker: Broker):
        self.name = name
        self.broker = broker
        self.consumers: dict[str, Consumer] = {}
        self._publish_registry: set[type[CloudEvent]] = set()

    def subscribe(
        self,
        topic: str,
        name: str | None = None,
        **extra: Any,
    ):
        def wrapper(func_or_cls: MessageHandlerT) -> MessageHandlerT:
            if callable(func_or_cls):
                consumer = Consumer(
                    service_name=self.name,
                    topic=topic,
                    name=name or func_or_cls.__name__,
                    fn=func_or_cls,  # type: ignore
                    **extra,
                )
            elif inspect.isclass(func_or_cls) and issubclass(
                func_or_cls, GenericConsumer
            ):
                consumer = func_or_cls(
                    service_name=self.name,
                    topic=topic,
                    name=name or func_or_cls.name,
                    **extra,
                )
            else:
                raise TypeError("Expected function or generic consumer")

            self.consumers[consumer.name] = consumer
            return func_or_cls

        return wrapper

    def publishes(self):
        def wrapper(cls: type[CloudEvent]):
            self._publish_registry.add(cls)
            return cls

        return wrapper

    async def publish_event(self, message: CloudEvent, **kwargs: Any) -> None:
        await self.broker.publish_event(message, **kwargs)

    async def publish(
        self,
        topic: str,
        data: Any | None = None,
        type_: type[CloudEvent] | str = "CloudEvent",
        **kwargs,
    ):
        await self.broker.publish(topic, data, type_, source=self.name, **kwargs)

    async def start(self) -> None:
        await self.broker.connect()
        await self.broker.dispatch_before("service_start", self)
        for consumer in self.consumers.values():
            asyncio.create_task(self.broker.start_consumer(consumer))
        await self.broker.dispatch_after("service_start", self)

    async def stop(self, *args, **kwargs) -> None:
        await self.broker.disconnect()


class ServiceGroup:
    def __init__(self, services: list[Service] | None = None):
        self.services = services or []

    def add_service(self, service: Service):
        self.services.append(service)

    async def start(self) -> None:
        await asyncio.gather(*[svc.start() for svc in self.services])

    async def stop(self) -> None:
        await asyncio.gather(
            *[svc.stop() for svc in self.services], return_exceptions=True
        )
