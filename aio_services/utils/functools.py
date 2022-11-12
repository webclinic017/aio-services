from __future__ import annotations

from random import uniform


def compute_backoff(
    attempts: int,
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
        backoff = int(backoff + uniform(0, backoff))  # nosec
    return attempts + 1, backoff
