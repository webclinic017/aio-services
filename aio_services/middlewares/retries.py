from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from aio_services.exceptions import Retry
from aio_services.middleware import Middleware
from aio_services.types import AbstractIncomingMessage, BrokerT, ConsumerP
from aio_services.utils.functools import compute_backoff


@dataclass(frozen=True)
class RetryConsumerOptions:
    # TODO: max_retries not always supported (e.g. rabbitmq)
    max_retries: int = 10
    min_backoff: int = 15
    max_backoff: int = 86400 * 7
    max_age: int | None = None
    retry_when: Callable[[int, Exception], Awaitable[bool]] | None = None
    throws: type[Exception] | tuple[type[Exception]] | None = None


class RetryMiddleware(Middleware[BrokerT]):
    """
    Retry Message Middleware
    """

    def __init__(self, default_retry_options: RetryConsumerOptions | None = None):
        self.default_retry_options = default_retry_options or RetryConsumerOptions()

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerP,
        message: AbstractIncomingMessage,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        if exc is None:
            return

        throws = consumer.options.get("throws")
        if throws and isinstance(exc, throws):
            return

        retries_so_far = broker.get_num_delivered(message)
        retry_when = consumer.options.get(
            "retry_when", self.default_retry_options.retry_when
        )
        max_retries = consumer.options.get(
            "max_retries", self.default_retry_options.max_retries
        )
        if (
            callable(retry_when)
            and not await retry_when(retries_so_far, exc)
            or retry_when is None
            and retries_so_far >= max_retries
        ):
            self.logger.error(f"Retry limit exceeded for message {message.id}.")
            await broker.ack(consumer, message)
        if isinstance(exc, Retry) and exc.delay is not None:
            delay = exc.delay
        else:
            _, delay = compute_backoff(
                retries_so_far,
                factor=consumer.options.get(
                    "min_backoff", self.default_retry_options.min_backoff
                ),
                max_backoff=consumer.options.get(
                    "max_backoff", self.default_retry_options.max_backoff
                ),
            )

        self.logger.info("Retrying message %r in %d milliseconds.", message.id, delay)
        await broker.nack(consumer, message)
