from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .broker import Broker
    from .service import Service


class ServiceRunner:
    def __init__(
        self,
        broker: Broker,
        services: Iterable[Service] | None = None,
        shutdown_cb=None,
    ):
        self.broker = broker
        self.services = {}
        if services:
            for s in services:
                self.services[s.name] = s
        self.shutdown_cb = shutdown_cb

    def add_service(self, service: Service):
        self.services[service.name] = service

    def get_service(self, name: str):
        return self.services[name]

    async def start(self):
        await self.broker.connect()
        tasks = []
        for service in self.services.values():
            for consumer in service.consumers.values():
                task = asyncio.create_task(
                    self.broker.start_consumer(service.qualname, consumer)
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

    async def stop(self, *args, **kwargs):
        if self.shutdown_cb:
            await self.shutdown_cb(*args, **kwargs)
        await self.broker.disconnect()

    def run(self, use_uvloop: bool = False, **kwargs):
        import aiorun

        aiorun.run(
            self.start(), shutdown_callback=self.stop, use_uvloop=use_uvloop, **kwargs
        )
