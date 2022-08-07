from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from aio_services.utils.mixins import ConsumerOptMixin, LoggerMixin

if TYPE_CHECKING:
    from aio_services.consumer import Consumer
    from aio_services.types import EventT, MessageT, BrokerT, COpts


class Middleware(LoggerMixin, ConsumerOptMixin[COpts], Generic[COpts, BrokerT]):
    async def before_broker_connect(self, broker: BrokerT):
        ...

    async def after_broker_connect(self, broker: BrokerT):
        ...

    async def before_broker_disconnect(self, broker: BrokerT):
        ...

    async def after_broker_disconnect(self, broker: BrokerT):
        ...

    async def before_consumer_start(self, broker: BrokerT, consumer: Consumer):
        ...

    async def after_consumer_start(self, broker: BrokerT, consumer: Consumer):
        ...

    async def before_ack(self, broker: BrokerT, message: EventT, raw_message: MessageT):
        ...

    async def after_ack(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
    ):
        ...

    async def before_nack(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
    ):
        ...

    async def after_nack(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
    ):
        ...

    async def before_publish(self, broker: BrokerT, message: EventT, **kwargs):
        ...

    async def after_publish(self, broker: BrokerT, message: EventT, **kwargs):
        ...

    async def after_skip_message(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
    ):
        ...

    async def before_process_message(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
    ):
        ...

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: Consumer,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        ...
