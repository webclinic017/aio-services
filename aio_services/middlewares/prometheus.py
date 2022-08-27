from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from uuid import UUID

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)

from aio_services.middleware import Middleware
from aio_services.utils.datetime import current_millis

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, EventT, MessageT


class PrometheusMiddleware(Middleware):
    def __init__(self, expose_metrics: bool = False):
        self.expose_metrics = expose_metrics
        registry = REGISTRY
        if (
            "prometheus_multiproc_dir" in os.environ
            or "PROMETHEUS_MULTIPROC_DIR" in os.environ
        ):
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        self.registry = registry
        self.in_progress = Gauge(
            "messages_in_progress",
            "Total number of messages being processed.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_messages = Counter(
            "messages_total",
            "Total number of messages processed.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_messages_published = Counter(
            "messages_published_total",
            "Total number of messages published",
            ["topic", "service"],
            registry=self.registry,
        )
        self.total_errored_messages = Counter(
            "message_error_total",
            "Total number of errored messages.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_rejected_messages = Counter(
            "message_rejected_total",
            "Total number of messages rejected",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.message_durations = Histogram(
            "message_duration_ms",
            "Time spend processing message",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.message_start_times: dict[UUID | str, int] = {}

    async def before_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        labels = (consumer.topic, consumer.service_name, consumer.name)
        self.in_progress.labels(*labels).inc()
        self.message_start_times[message.id] = current_millis()

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        labels = (consumer.topic, consumer.service_name, consumer.name)
        self.in_progress.labels(*labels).dec()
        self.total_messages.labels(*labels).inc()
        if exc:
            self.total_errored_messages.labels(*labels).inc()

        message_start_time = self.message_start_times.pop(message.id, current_millis())
        message_duration = current_millis() - message_start_time
        self.message_durations.labels(*labels).observe(message_duration)

    after_skip_message = after_process_message

    async def after_publish(self, broker: BrokerT, message: EventT, **kwargs):
        self.total_messages_published.labels(message.topic, message.source).inc()

    async def after_nack(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        labels = (consumer.topic, consumer.service_name, consumer.name)
        self.total_rejected_messages.labels(*labels).inc()

    @property
    def latest(self):
        return generate_latest(self.registry)

    async def after_broker_connect(self, broker: BrokerT):
        if self.expose_metrics:
            pass  # RUN http server