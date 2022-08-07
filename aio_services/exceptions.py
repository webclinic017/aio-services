class BrokerError(Exception):
    pass


class MessageError(BrokerError):
    def __init__(self, message):
        self.message = message


class DecodeError(Exception):
    def __init__(self, data, error):
        self.data = data
        self.error = error


class Skip(Exception):
    """Raise exception to skip message without processing and/or retrying"""


class Fail(Exception):
    """Fail message without retrying"""
