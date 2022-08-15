from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from aio_services.middleware import Middleware

if TYPE_CHECKING:
    from aio_services.types import BrokerT, ConsumerT, EventT, MessageT


class CurrentMessageMiddleware(Middleware):
    def __init__(self):
        self._current_message: ContextVar[MessageT] = ContextVar("current_message")
        self._tokens = {}

    @property
    def current_message(self) -> MessageT:
        return self._current_message.get()

    async def before_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
    ):
        token = self._current_message.set(raw_message)
        self._tokens[message.id] = token

    async def after_process_message(
        self,
        broker: BrokerT,
        consumer: ConsumerT,
        message: EventT,
        raw_message: MessageT,
        result: Any | None = None,
        exc: Exception | None = None,
    ):
        try:
            self._current_message.reset(self._tokens.pop(message.id))
        except Exception:
            pass
