from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aio_services.middleware import Middleware
from aio_services.utils.asyncio import run_async

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, EventT, F, MessageT


class ErrorHandlerMiddleware(Middleware):
    def __init__(self, errors: type[Exception] | tuple[type[Exception]], callback: F):
        if not asyncio.iscoroutinefunction(callback):
            callback = run_async(callback)
        self.cb = callback
        self.exc = errors

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        if exc and isinstance(exc, self.exc):
            await self.cb(message, exc)