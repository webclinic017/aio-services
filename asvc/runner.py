import asyncio

import aiorun

from .service import Service


class ServiceRunner:
    """Utility class for running multiple services in one process"""

    def __init__(self, *services: Service):
        self.services = services

    def run(self, use_uvloop: bool = False, **kwargs):
        aiorun.run(
            self._run(), shutdown_callback=self._stop, use_uvloop=use_uvloop, **kwargs
        )

    async def _run(self):
        await asyncio.gather(s.start for s in self.services)

    async def _stop(self, *args, **kwargs):
        await asyncio.gather(s.stop for s in self.services)
