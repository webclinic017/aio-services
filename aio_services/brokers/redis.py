from typing import Type, Optional, List
import aioredis
from aio_services.broker import AbstractBroker, AbstractConsumer
from aio_services.middleware import Middleware
from aio_services.types import Encoder


class RedisConsumer(AbstractConsumer):
    async def _consume(self, broker: "RedisBroker") -> None:
        pubsub = broker.redis.pubsub()
        await pubsub.subscribe(self.topic, **self.options)


class RedisBroker(AbstractBroker):
    def __init__(
        self,
        *,
        url: str,
        group_id: str,
        encoder: Optional[Encoder] = None,
        middlewares: Optional[List[Middleware]] = None,
        **options
    ):
        super().__init__(
            group_id=group_id, encoder=encoder, middlewares=middlewares, **options
        )
        self.url = url
        self._redis = None

    @property
    def redis(self) -> aioredis.Redis:
        assert self._redis is not None, "Not connected"
        return self._redis

    async def connect(self):
        self._redis = aioredis.from_url(url=self.url, **self.options)

    async def _publish(self, topic: str, message, **kwargs):
        await self.redis.publish(topic, message)

    @property
    def consumer_class(self) -> Type[AbstractConsumer]:
        return RedisConsumer
