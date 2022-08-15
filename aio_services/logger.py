import inspect
import logging
from typing import Type, Union


def get_logger(module: str, name: Union[str, Type]) -> logging.Logger:
    if inspect.isclass(name):
        name = name.__name__

    return logging.getLogger(f"{module}.{name}")
