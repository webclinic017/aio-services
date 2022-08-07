from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Generic

from aio_services.logger import get_logger
from aio_services.models import BaseConsumerOptions
from aio_services.types import COpts
from aio_services.utils.functools import method_cache

if TYPE_CHECKING:
    import logging

    from aio_services.consumer import Consumer


class ConsumerOptMixin(Generic[COpts]):
    ConsumerOptions: type[COpts] = BaseConsumerOptions

    @method_cache
    def get_consumer_options(self, consumer: Consumer) -> COpts:
        model = self.ConsumerOptions.parse_obj(consumer.options)
        return model


class LoggerMixin:
    @cached_property
    def logger(self) -> logging.Logger:
        return get_logger(__name__, type(self))
