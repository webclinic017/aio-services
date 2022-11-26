from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from asvc.exceptions import Retry
from asvc.middleware import Middleware
from asvc.utils.datetime import utc_now

if TYPE_CHECKING:
    from asvc.broker import Broker
    from asvc.consumer import Consumer
    from asvc.models import CloudEvent


@dataclass(frozen=True)
class RetryConsumerOptions:
    """
    Retries based on backoff and max_age, as not every broker provides info about
    number of times that message was delivered
    """

    backoff_factor: int = 5
    max_age: int = 60
    retry_when: Callable[[int, Exception], Awaitable[bool]] | None = None
    throws: type[Exception] | tuple[type[Exception]] | None = None


class RetryMiddleware(Middleware):
    """
    Retry Message Middleware
    """

    def __init__(self, default_retry_options: RetryConsumerOptions | None = None):
        self.default_retry_options = default_retry_options or RetryConsumerOptions()

    async def after_process_message(
        self,
        broker: Broker,
        consumer: Consumer,
        message: CloudEvent,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        if exc is None:
            return

        throws = consumer.options.get("throws")
        if throws and isinstance(exc, throws):
            return

        retry_when = consumer.options.get(
            "retry_when", self.default_retry_options.retry_when
        )
        message_age = (utc_now() - message.time).seconds
        max_age = consumer.options.get("max_age", self.default_retry_options.max_age)
        if (
            callable(retry_when)
            and not await retry_when(message_age, exc)
            or retry_when is None
            and message_age >= max_age
        ):
            self.logger.error(f"Retry limit exceeded for message {message.id}.")
            await broker.ack(consumer, message)
        if isinstance(exc, Retry) and exc.delay is not None:
            delay = exc.delay
        else:
            delay = consumer.options.get(
                "backoff", self.default_retry_options.backoff_factor
            )

        self.logger.info("Retrying message %r in %d milliseconds.", message.id, delay)
        await broker.nack(consumer, message)

    @staticmethod
    def compute_backoff(
        message_age: int,
        *,
        backoff_factor: int = 5,
    ) -> int:
        return message_age * backoff_factor
