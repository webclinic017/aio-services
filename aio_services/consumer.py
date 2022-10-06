from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, cast, get_type_hints

from aio_services.logger import get_logger
from aio_services.types import EventT
from aio_services.utils.asyncio import run_async

if TYPE_CHECKING:
    from aio_services.types import HandlerT


class BaseConsumer(ABC, Generic[EventT]):
    event_type: EventT

    def __init__(
        self,
        *,
        service_name: str,
        name: str,
        topic: str,
        timeout: int = 120,
        **options: Any,
    ):
        self.service_name = service_name
        self.name = name
        self.topic = topic
        self.timeout = timeout
        self.options: dict[str, Any] = options
        self.logger = get_logger(__name__, f"{service_name}:{self.name}")

    @abstractmethod
    async def process(self, message: EventT):
        raise NotImplementedError


class Consumer(BaseConsumer[EventT]):
    def __init__(
        self,
        *,
        service_name: str,
        name: str | None = None,
        topic: str,
        fn: HandlerT,
        concurrency: int = 10,
        **options: Any,
    ):
        super().__init__(
            service_name=service_name, name=name or fn.__name__, topic=topic, **options
        )
        event_type = get_type_hints(fn).get("message")
        assert event_type, f"Unable to resolve type hint for 'message' in {fn.__name__}"
        self.event_type = cast(EventT, event_type)
        if not asyncio.iscoroutinefunction(fn):
            fn = run_async(fn)
        self.fn = fn
        self.concurrency = concurrency
        self._sem = asyncio.Semaphore(self.concurrency)

    async def process(self, message: EventT):
        async with self._sem:
            # TODO: add timeout async with async_timeout.timeout(self.timeout):
            self.logger.info(f"Processing message {message.id}")
            result = await self.fn(message)
            self.logger.info(f"Finished processing {message.id}")
            return result


class GenericConsumer(BaseConsumer[EventT], ABC):
    def __init__(self, *, service_name: str, name: str, topic: str, **options: Any):
        super().__init__(service_name=service_name, name=name, topic=topic, **options)

        event_type = get_type_hints(self.process).get("message")
        assert event_type, "Unable to resolve type hint for 'message' in .process()"
        self.event_type = cast(EventT, event_type)
