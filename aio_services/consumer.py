from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, cast, get_type_hints

from aio_services.logger import get_logger
from aio_services.types import FT, IncomingMessage, T
from aio_services.utils.asyncio import run_async


class AbstractConsumer(ABC, Generic[IncomingMessage, T]):
    event_type: T

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
        self.logger = get_logger(__name__, self.full_name)

    @property
    def full_name(self):
        return f"{self.service_name}:{self.name}"

    def validate_message(self, message: Any) -> T:
        return self.event_type.parse_obj(message)

    @abstractmethod
    async def process(self, message: IncomingMessage):
        raise NotImplementedError


class Consumer(AbstractConsumer):
    def __init__(
        self,
        *,
        service_name: str,
        name: str,
        topic: str,
        fn: FT,
        **options: Any,
    ) -> None:
        super().__init__(service_name=service_name, name=name, topic=topic, **options)
        event_type = get_type_hints(fn).get("message")
        assert event_type, f"Unable to resolve type hint for 'message' in {fn.__name__}"
        self.event_type = event_type
        if not asyncio.iscoroutinefunction(fn):
            fn = run_async(fn)
        self.fn = fn

    async def process(self, message: IncomingMessage) -> Any | None:
        self.logger.info(f"Processing message {message.id}")
        result = await self.fn(message)
        self.logger.info(f"Finished processing {message.id}")
        return result


class GenericConsumer(AbstractConsumer, ABC):
    name: str | None = None

    def __init_subclass__(cls, **kwargs):
        if not asyncio.iscoroutinefunction(cls.process):
            cls.process = run_async(cls.process)

    def __init__(self, *, service_name: str, topic: str, **options: Any) -> None:
        super().__init__(
            service_name=service_name,
            topic=topic,
            name=self.name or type(self).__name__,
            **options,
        )

        event_type = get_type_hints(self.process).get("message")
        assert event_type, "Unable to resolve type hint for 'message' in .process()"
        self.event_type = cast(IncomingMessage, event_type)
