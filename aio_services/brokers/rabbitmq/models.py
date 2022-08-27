from typing import Dict, Any

from aio_services import BaseConsumerOptions


class RabbitmqConsumerOptions(BaseConsumerOptions):
    prefetch_count: int = 10
    queue_options: Dict[str, Any] = {}
