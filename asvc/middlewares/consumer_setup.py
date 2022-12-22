from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from asvc import Consumer, Middleware

if TYPE_CHECKING:
    from asvc.broker import Broker

ON_STARTUP_ATTR = "__on_startup"


def on_startup(func):
    setattr(func, ON_STARTUP_ATTR, True)


class ConsumerSetupMiddleware(Middleware):
    @staticmethod
    def _predicate(obj):
        return getattr(obj, ON_STARTUP_ATTR, False)

    async def before_consumer_start(self, broker: Broker, consumer: Consumer) -> None:
        for name, func in inspect.getmembers(consumer, self._predicate):
            await func()
