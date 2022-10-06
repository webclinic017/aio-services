import inspect
import logging
from typing import Type, Union


def get_logger(module: str, name: Union[str, Type]) -> logging.Logger:
    if inspect.isclass(name):
        name = name.__name__

    return logging.getLogger(f"{module}.{name}")


class LoggerMixin:
    logger: logging.Logger

    def __init_subclass__(cls, **kwargs):
        cls.logger = get_logger(__name__, cls)
