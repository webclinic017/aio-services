# from __future__ import annotations
#
# from typing import TYPE_CHECKING, Any
#
# import aioredis
#
# from asvc.broker import BaseBroker
# from asvc.types import AbstractMessage, ConsumerP, RawMessage
#
# if TYPE_CHECKING:
#     from asvc.middleware import Middleware
#     from asvc.types import Encoder
#
#
# class RedisBroker(BaseBroker[Any, dict[str, str]]):
#     def __init__(
#         self,
#         *,
#         url: str,
#         encoder: Encoder | None = None,
#         middlewares: list[Middleware] | None = None,
#         **options: Any,
#     ) -> None:
#         super().__init__(encoder=encoder, middlewares=middlewares, **options)
#         self.url = url
#         self._redis = None
#
#     def parse_incoming_message(self, message: RawMessage) -> Any:
#         pass
#
#     @property
#     def is_connected(self) -> bool:
#         return self.redis.connection.is_connected
#
#     async def _start_consumer(self, consumer: ConsumerP):
#         handler = self.get_handler(consumer)
#         psub = self.redis.pubsub()
#
#         while True:
#             message = await psub.get_message(ignore_subscribe_messages=True)
#             if message:
#                 await handler(message)
#
#     @staticmethod
#     def get_message_data(message) -> bytes:
#         return message.get("data", None)
#
#     async def _disconnect(self):
#         await self.redis.close()
#
#     @property
#     def redis(self) -> aioredis.Redis:
#         assert self._redis is not None, "Not connected"
#         return self._redis
#
#     async def _connect(self):
#         self._redis = aioredis.from_url(url=self.url, **self.options)
#
#     async def _publish(self, message: AbstractMessage, **kwargs) -> None:
#         data = self.encoder.encode(message)
#         await self.redis.publish(message.topic, data)
