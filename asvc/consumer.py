from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, get_type_hints

from asvc.logger import get_logger
from asvc.types import FT, MessageHandlerT, T
from asvc.utils.functools import run_async

if TYPE_CHECKING:
    from .models import CloudEvent


@dataclass
class ForwardResponse:
    topic: str
    as_type: str = "CloudEvent"


class Consumer(ABC, Generic[T]):
    event_type: T

    def __init__(
        self,
        *,
        name: str,
        topic: str,
        timeout: int = 120,
        dynamic: bool = False,
        forward_response: ForwardResponse | None = None,
        **options: Any,
    ):
        self.name = name
        self.topic = topic
        self.timeout = timeout
        self.dynamic = dynamic
        self.forward_response = forward_response
        self.options: dict[str, Any] = options
        self.logger = get_logger(__name__, self.name)

    def validate_message(self, message: Any) -> T:
        return self.event_type.parse_obj(message)

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def process(self, message: CloudEvent):
        raise NotImplementedError


class FnConsumer(Consumer[T]):
    def __init__(
        self,
        *,
        fn: FT,
        name: str,
        topic: str,
        **options: Any,
    ) -> None:
        super().__init__(name=name or fn.__name__, topic=topic, **options)
        event_type = get_type_hints(fn).get("message")
        assert event_type, f"Unable to resolve type hint for 'message' in {fn.__name__}"
        self.event_type = event_type
        if not asyncio.iscoroutinefunction(fn):
            fn = run_async(fn)
        self.fn = fn

    async def process(self, message: T) -> Any | None:
        self.logger.info(f"Processing message {message.id}")
        result = await self.fn(message)
        self.logger.info(f"Finished processing {message.id}")
        return result

    @property
    def description(self) -> str:
        return self.fn.__doc__ or ""


class GenericConsumer(Consumer[T], ABC):
    name: str = "Generic Consumer"

    def __init__(self, *, name: str, topic: str, **options: Any):

        super().__init__(name=name or type(self).name, topic=topic, **options)

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "name"):
            setattr(cls, "name", cls.__name__)
        cls.event_type: T = get_type_hints(cls.process).get("message")
        if not asyncio.iscoroutinefunction(cls.process):
            cls.process = run_async(cls.process)

    @property
    def description(self) -> str:
        return self.__doc__ or ""


class ConsumerGroup:
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.consumers: dict[str, Consumer] = {}

    def add_consumer(self, consumer: Consumer) -> None:
        self.consumers[consumer.name] = consumer

    def add_consumer_group(self, other: ConsumerGroup) -> None:
        self.consumers.update(other.consumers)

    def subscribe(self, topic, **options):
        def wrapper(func_or_cls: MessageHandlerT) -> MessageHandlerT:
            # if isinstance(topic, T): topic = self.broker.resolve_topic(topic)
            if inspect.isclass(func_or_cls) and issubclass(
                func_or_cls, GenericConsumer
            ):
                consumer = func_or_cls(
                    topic=topic,
                    **options,
                )
            elif callable(func_or_cls):
                consumer = FnConsumer(
                    topic=topic,
                    fn=func_or_cls,  # type: ignore
                    **options,
                )
            else:
                raise TypeError("Expected function or GenericConsumer")

            self.consumers[consumer.name] = consumer
            return func_or_cls

        return wrapper
