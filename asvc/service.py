from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from .consumer import Consumer, GenericConsumer
from .logger import LoggerMixin
from .models import CloudEvent, PublishInfo

if TYPE_CHECKING:
    from .types import MessageHandlerT, TagMeta


class Service(LoggerMixin):
    """Logical group of consumers. Provides group (queue) name and handles versioning"""

    def __init__(
        self,
        name: str,
        title: str | None = None,
        version: str = "1.0.0",
        description: str = "",
        use_versioning: bool = False,
        tags_metadata: list[TagMeta] = None,
        consumers: dict[str, Consumer] = None,
    ):
        self.name = name
        self.title = title or name.title()
        self.version = version
        self.qualname = f"{self.name}:{self.version}" if use_versioning else self.name
        self.description = description
        self.tags_metadata = tags_metadata or []
        self.consumers = consumers or {}
        self._publish_registry: dict[str, PublishInfo] = {}

    def __hash__(self):
        return hash((self.name, self.version))

    def __eq__(self, other: Service):
        if type(self) != type(other):
            return False
        return self.name == other.name and self.version == other.version

    def subscribe(
        self,
        topic: str,
        **extra: Any,
    ):
        def wrapper(func_or_cls: MessageHandlerT) -> MessageHandlerT:
            if callable(func_or_cls):
                consumer = Consumer(
                    topic=topic,
                    fn=func_or_cls,  # type: ignore
                    **extra,
                )
            elif inspect.isclass(func_or_cls) and issubclass(
                func_or_cls, GenericConsumer
            ):
                consumer = func_or_cls(
                    topic=topic,
                    **extra,
                )
            else:
                raise TypeError("Expected function or generic consumer")

            self.consumers[consumer.name] = consumer
            return func_or_cls

        return wrapper

    def add_consumer(self, consumer: Consumer) -> None:
        self.consumers[consumer.name] = consumer

    def publishes(self, topic: str, **kwargs):
        def wrapper(cls: type[CloudEvent]) -> type[CloudEvent]:
            self._publish_registry[cls.__name__] = PublishInfo(
                topic=topic, event_type=cls, kwargs=kwargs
            )
            return cls

        return wrapper

    @property
    def publish_registry(self) -> dict[str, PublishInfo]:
        return self._publish_registry
