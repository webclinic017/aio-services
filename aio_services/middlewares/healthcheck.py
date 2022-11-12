import asyncio
import os
from pathlib import Path
from typing import Awaitable, Callable, Optional, Sequence

from aio_services.middleware import Middleware
from aio_services.types import BrokerT


class HealthCheckMiddleware(Middleware):
    """Middleware for performing basic health checks on broker"""

    BASE_DIR = os.getenv("HEALTHCHECK_DIR", "/tmp")  # nosec

    def __init__(
        self,
        interval: int = 30,
        file_mode: bool = False,
        checkers: Optional[Sequence[Callable[..., Awaitable[bool]]]] = None,
    ):
        self.interval = interval  # 30s by default
        self.file_mode = file_mode
        self._checkers = checkers
        self._broker = None
        self._task = None

    async def after_broker_connect(self, broker: BrokerT):
        self._broker = broker
        if self.file_mode:
            self._task = asyncio.create_task(self._run_forever())

    async def before_broker_disconnect(self, broker: BrokerT):
        if self.file_mode:
            self._task.cancel()
            await self._task

    async def _run_forever(self):
        p = Path(os.path.join(self.BASE_DIR, "healthy"))
        p.touch(exist_ok=True)
        try:
            while True:
                is_connected = self._broker.is_connected
                if not is_connected:
                    p.rename(os.path.join(self.BASE_DIR, "unhealthy"))
                    break
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            pass

    async def get_health_status(self) -> bool:
        return self._broker.is_connected
