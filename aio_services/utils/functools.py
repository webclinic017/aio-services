from __future__ import annotations
import functools
import weakref
from random import uniform
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from aio_services.types import F


def method_cache(func: F) -> F:
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        # We're storing the wrapped method inside the instance. If we had
        # a strong reference to self the instance would never die.
        self_weak = weakref.ref(self)

        @functools.wraps(func)
        @functools.cache
        def cached_method(*args, **kwargs):
            return func(self_weak(), *args, **kwargs)

        setattr(self, func.__name__, cached_method)
        return cached_method(*args, **kwargs)

    return cast(F, wrapped)


def compute_backoff(
    attempts,
    *,
    factor: int = 5,
    jitter: bool = True,
    max_backoff: int = 2000,
    max_exponent: int = 32,
) -> tuple[int, int]:
    exponent = min(attempts, max_exponent)
    backoff = min(factor * 2**exponent, max_backoff)
    if jitter:
        backoff /= 2
        backoff = int(backoff + uniform(0, backoff))
    return attempts + 1, backoff
