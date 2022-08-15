from typing import Optional, Callable, Union, Awaitable

from nats.js.api import ConsumerConfig
from typing_extensions import Type
from aio_services import BaseConsumerOptions


class NatsConsumerOptions(BaseConsumerOptions):
    max_msgs: Optional[int] = None
    pending_msgs_limit: Optional[int] = None
    pending_bytes_limit: Optional[int] = None
    prefetch_count: int = 10
    timeout: int = 60
    config: Optional[ConsumerConfig] = None


class JetStreamResultConsumerOptions(BaseConsumerOptions):
    store_results: bool = False


class RetryConsumerOptions(BaseConsumerOptions):
    max_retries: int = 10
    min_backoff: int = 15
    max_backoff: int = 86400 * 7
    max_age: Optional[int] = None
    retry_when: Optional[Callable[[int, Exception], Awaitable[bool]]] = None
    throws: Optional[Union[Type[Exception], tuple[Type[Exception]]]] = None
