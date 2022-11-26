# from __future__ import annotations
#
# from typing import TYPE_CHECKING, Any
# from uuid import UUID
#
# from asvc.middleware import Middleware
# from asvc.models import BaseConsumerOptions
#
# if TYPE_CHECKING:
#     from asvc.backends.redis import RedisBroker
#     from asvc.broker import Broker
#     from asvc.types import ConsumerT, EventT, MessageT
#
#
# class RedisStoreResultConsumerOptions(BaseConsumerOptions):
#     store_results: bool = False
#
#
# class RedisResultMiddleware(Middleware):
#     ConsumerOptions = RedisStoreResultConsumerOptions
#
#     def __init__(self, prefix: str = "results", ttl: int = 3600):
#         self.prefix = prefix
#         self.ttl = ttl
#         self._broker: RedisBroker | None = None
#
#     @property
#     def broker(self) -> RedisBroker:
#         assert self._broker
#         return self._broker
#
#     @property
#     def supported_backends(self) -> type[Broker] | tuple[type[Broker]]:
#         return RedisBroker
#
#     async def after_broker_connect(self, broker: RedisBroker):
#         self._broker = broker
#
#     async def after_process_message(
#         self,
#         broker: RedisBroker,
#         consumer: ConsumerT,
#         message: EventT,
#         raw_message: MessageT,
#         result: Any | None = None,
#         exc: Exception | None = None,
#     ):
#         if exc is None:
#             opt = self.get_consumer_options(consumer)
#             if opt.store_results:
#                 value = broker.encoder.encode(message)
#                 key = f"{self.prefix}:{message.id}"
#                 await broker.redis.setex(key, self.ttl, value)
#
#     async def get_result(self, message_id: UUID):
#         key = f"{self.prefix}:{message_id}"
#         data = await self.broker.redis.get(key)
#         if data:
#             return self.broker.encoder.decode(data)
