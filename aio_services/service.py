from typing import List, Optional

from aio_services.broker import AbstractBroker
from aio_services.middleware import Middleware


class AioService:
    def __init__(
        self,
        name: str,
        broker: AbstractBroker,
        middlewares: Optional[List[Middleware]] = None,
    ):
        self.name = name
        self.broker = broker
        self.middlewares = middlewares or []

    def subscribe(self, *args, **kwargs):
        return self.broker.subscribe(*args, **kwargs)

    async def publish(self, topic: str, message, **kwargs):
        return await self.broker.publish(topic, message, **kwargs)
