#
# from __future__ import annotations
#
# import socket
# from contextvars import ContextVar
# from typing import TYPE_CHECKING, Any
#
# from asvc.middleware import Middleware
# from opentelemetry import trace
#
# if TYPE_CHECKING:
#     from asvc.consumer import Consumer
#     from asvc.types import BrokerT, EventT, MessageT
#     from asvc.service import Service
#     from opentelemetry.sdk.trace import TracerProvider
#
#
# class OpenTelemetryMiddleware(Middleware):
#     def __init__(self):
#         self.tracer = trace.get_tracer(__name__)
#         self.ctx = ContextVar("ctx")
#
#     async def before_service_start(self, broker: BrokerT, service: Service):
#         resource = {
#             "service.name": service.name,
#             "service.instance.id": socket.gethostname()
#         }
#
#     async def before_broker_connect(self, broker: BrokerT):
#         ...
#
#     async def before_process_message(
#         self,
#         broker: BrokerT,
#         consumer: Consumer,
#         message: EventT,
#         raw_message: MessageT,
#     ):
#         ...
#
#     async def after_process_message(
#         self,
#         broker: BrokerT,
#         consumer: Consumer,
#         message: EventT,
#         raw_message: MessageT,
#         result: Any | None = None,
#         exc: Exception | None = None,
#     ):
#         ...
#
#     async def before_publish(self, broker: BrokerT, message: EventT, **kwargs):
#         ...
