from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, get_type_hints

from asvc.logger import get_logger
from asvc.types import FT, T
from asvc.utils.functools import run_async

if TYPE_CHECKING:
    from asvc.models import CloudEvent


@dataclass
class ForwardResponse:
    topic: str
    as_type: str = "CloudEvent"


class AbstractConsumer(ABC, Generic[T]):
    event_type: T

    def __init__(
        self,
        *,
        service_name: str,
        name: str,
        topic: str,
        timeout: int = 120,
        dynamic: bool = False,
        forward_response: ForwardResponse | None = None,
        **options: Any,
    ):
        self.service_name = service_name
        self.name = name
        self.topic = topic
        self.timeout = timeout
        self.dynamic = dynamic
        self.forward_response = forward_response
        self.options: dict[str, Any] = options
        self.logger = get_logger(__name__, self.full_name)

    @property
    def full_name(self):
        return f"{self.service_name}:{self.name}"

    def validate_message(self, message: Any) -> T:
        return self.event_type.parse_obj(message)

    @abstractmethod
    async def process(self, message: CloudEvent):
        raise NotImplementedError


class Consumer(AbstractConsumer):
    def __init__(
        self,
        *,
        fn: FT,
        **extra: Any,
    ) -> None:
        super().__init__(**extra)
        event_type = get_type_hints(fn).get("message")
        assert event_type, f"Unable to resolve type hint for 'message' in {fn.__name__}"
        self.event_type = event_type
        if not asyncio.iscoroutinefunction(fn):
            fn = run_async(fn)
        self.fn = fn

    async def process(self, message: CloudEvent) -> Any | None:
        self.logger.info(f"Processing message {message.id}")
        result = await self.fn(message)
        self.logger.info(f"Finished processing {message.id}")
        return result


class GenericConsumer(AbstractConsumer, ABC):
    name: str

    def __init_subclass__(cls, **kwargs):
        cls.event_type = get_type_hints(cls.process).get("message")
        if not asyncio.iscoroutinefunction(cls.process):
            cls.process = run_async(cls.process)
