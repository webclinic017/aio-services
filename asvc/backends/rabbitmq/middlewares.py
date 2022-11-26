# from __future__ import annotations
#
# from typing import TYPE_CHECKING
#
# from aio_pika import ExchangeType
#
# from asvc.backends.rabbitmq.broker import RabbitmqBroker
# from asvc.middleware import Middleware
#
# if TYPE_CHECKING:
#     from asvc.types import ConsumerT
#
#
# class DLXMiddleware(Middleware[RabbitmqBroker]):
#     def __init__(self, dlx_name: str = "dlx"):
#         self.dlx_name = dlx_name
#         self._dlx_exchange = None
#
#     async def after_broker_connect(self, broker: RabbitmqBroker):
#         channel = await broker.connection.channel()
#         self._dlx_exchange = await channel.declare_exchange(
#             name=self.dlx_name, type=ExchangeType.HEADERS, auto_delete=True
#         )
#
#     async def after_consumer_start(self, broker: RabbitmqBroker, consumer: ConsumerT):
#         await broker.queues[consumer.name].bind(
#             self._dlx_exchange, "", arguments={"From": consumer.topic, "x-match": "any"}
#         )
