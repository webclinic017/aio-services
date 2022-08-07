from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Generic, cast, get_type_hints

from aio_services.logger import get_logger
from aio_services.utils.asyncio import run_async
from aio_services.types import EventT

if TYPE_CHECKING:
    from aio_services.types import HandlerT


class Consumer(Generic[EventT]):
    def __init__(
        self,
        *,
        service_name: str,
        topic: str,
        fn: HandlerT,
        name: str | None = None,
        concurrency: int = 10,
        **options: Any,
    ):

        event_type = get_type_hints(fn).get("message")
        assert event_type, f"Unable to resolve type hint for 'message' in {fn.__name__}"
        self.event_type = cast(EventT, event_type)
        self.service_name = service_name
        self.topic = topic
        if not asyncio.iscoroutinefunction(fn):
            fn = run_async(fn)
        self.fn = fn
        self.name = name or fn.__name__
        self.concurrency = concurrency
        self.options = options
        self._sem = asyncio.Semaphore(self.concurrency)
        self.logger = get_logger(__name__, f"{service_name}:{self.name}")

    async def process(self, message: EventT):
        async with self._sem:
            return await self.fn(message)
