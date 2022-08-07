# from __future__ import annotations
#
# import asyncio
# from collections import defaultdict
# from typing import TYPE_CHECKING, Sequence
#
# from aio_services.broker import Broker
#
# if TYPE_CHECKING:
#     from aio_services.consumer import Consumer
#     from aio_services.types import EventT, MessageT
#
#
# class StubBroker(Broker[bytes]):
#     def __init__(self, *, url: str | Sequence[str], **options):
#         super().__init__(url=url, **options)
#         self.topics: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
#         self._stopped = False
#
#     @staticmethod
#     def get_message_data(message: MessageT) -> bytes:
#         return message
#
#     async def _disconnect(self) -> None:
#         self._stopped = True
#
#     async def _start_consumer(self, consumer: Consumer):
#         queue = self.topics[consumer.topic]
#         handler = self.get_handler(consumer)
#         while not self._stopped:
#             message = await queue.get()
#             await handler(message)
#             queue.task_done()
#
#     async def _connect(self) -> None: ...
#
#     async def _publish(self, message: EventT, **kwargs) -> None:
#         topic = self.topics[message.topic]
#         data = self.encoder.encode(message)
#         await topic.put(data)
