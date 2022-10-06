from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from aio_services.logger import LoggerMixin
from aio_services.types import BrokerT

if TYPE_CHECKING:
    from aio_services.service import Service
    from aio_services.types import ConsumerT, EventT, MessageT


class Middleware(Generic[BrokerT], LoggerMixin):
    async def before_service_start(self, broker: BrokerT, service: Service):
        """Called before service starts"""

    async def after_service_start(self, broker: BrokerT, service: Service):
        """Called after service starts"""

    async def before_broker_connect(self, broker: BrokerT):
        """Called before broker connects"""

    async def after_broker_connect(self, broker: BrokerT):
        """Called after broker connects"""

    async def before_broker_disconnect(self, broker: BrokerT):
        """Called before broker disconnects"""

    async def after_broker_disconnect(self, broker: BrokerT):
        """Called after broker disconnects"""

    async def before_consumer_start(self, broker: BrokerT, consumer: ConsumerT):
        """Called before consumer is started"""

    async def after_consumer_start(self, broker: BrokerT, consumer: ConsumerT):
        """Called after consumer is started"""

    async def before_ack(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called before message is acknowledged"""

    async def after_ack(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called after message is acknowledged"""

    async def before_nack(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called before message is rejected"""

    async def after_nack(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called after message is rejected"""

    async def before_publish(self, broker: BrokerT, message: EventT, **kwargs):
        """Called before message is published"""

    async def after_publish(self, broker: BrokerT, message: EventT, **kwargs):
        """Called after message is published"""

    async def after_skip_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called after message is skipped by the middleware"""

    async def before_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        """Called before message is processed"""

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        """Called after message is processed (but not acknowledged/rejected yet)"""
