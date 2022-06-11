import logging

logger = logging.getLogger("AS")


class LogMixin:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
