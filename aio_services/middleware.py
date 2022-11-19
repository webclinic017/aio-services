from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aio_services.logger import LoggerMixin

if TYPE_CHECKING:
    from aio_services.broker import Broker
    from aio_services.consumer import Consumer
    from aio_services.models import CloudEvent
    from aio_services.service import Service


class Middleware(LoggerMixin):
    async def before_service_start(self, broker: Broker, service: Service) -> None:
        """Called before service starts"""

    async def after_service_start(self, broker: Broker, service: Service) -> None:
        """Called after service starts"""

    async def before_broker_connect(self, broker: Broker) -> None:
        """Called before broker connects"""

    async def after_broker_connect(self, broker: Broker) -> None:
        """Called after broker connects"""

    async def before_broker_disconnect(self, broker: Broker) -> None:
        """Called before broker disconnects"""

    async def after_broker_disconnect(self, broker: Broker) -> None:
        """Called after broker disconnects"""

    async def before_consumer_start(self, broker: Broker, consumer: Consumer) -> None:
        """Called before consumer is started"""

    async def after_consumer_start(self, broker: Broker, consumer: Consumer) -> None:
        """Called after consumer is started"""

    async def before_ack(
        self,
        broker: Broker,
        consumer: Consumer,
        message: CloudEvent,
    ) -> None:
        """Called before message is acknowledged"""

    async def after_ack(
        self,
        broker: Broker,
        consumer: Consumer,
        message: CloudEvent,
    ) -> None:
        """Called after message is acknowledged"""

    async def before_nack(
        self, broker: Broker, consumer: Consumer, message: CloudEvent
    ) -> None:
        """Called before message is rejected"""

    async def after_nack(
        self, broker: Broker, consumer: Consumer, message: CloudEvent
    ) -> None:
        """Called after message is rejected"""

    async def before_publish(
        self, broker: Broker, message: CloudEvent, **kwargs
    ) -> None:
        """Called before message is published"""

    async def after_publish(
        self, broker: Broker, message: CloudEvent, **kwargs
    ) -> None:
        """Called after message is published"""

    async def after_skip_message(
        self, broker: Broker, consumer: Consumer, message: CloudEvent
    ) -> None:
        """Called after message is skipped by the middleware"""

    async def before_process_message(
        self, broker: Broker, consumer: Consumer, message: CloudEvent
    ) -> None:
        """Called before message is processed"""

    async def after_process_message(
        self,
        broker: Broker,
        consumer: Consumer,
        message: CloudEvent,
        result: Any | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Called after message is processed (but not acknowledged/rejected yet)"""
