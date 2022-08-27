from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aio_services.types import MessageT


class BrokerError(Exception):
    pass


class MessageError(BrokerError):
    def __init__(self, message: MessageT):
        self.message = message


class DecodeError(Exception):
    def __init__(self, data: bytes, error):
        self.data = data
        self.error = error


class Skip(Exception):
    """Raise exception to skip message without processing and/or retrying"""


class Fail(Exception):
    """Fail message without retrying"""


class Retry(Exception):
    """
    Utility exception for retrying message.
    Handling must be implemented in middleware
    """

    def __init__(self, delay: int | None = None):
        self.delay = delay