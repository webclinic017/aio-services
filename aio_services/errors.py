class MiddlewareError(Exception):
    ...


class MessageError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message) or repr(self.message)


class SkipMessage(MiddlewareError):
    ...


# class DecodeError(MessageError):
#     def __init__(self, message, data, error):
#         super().__init__(message)
#         self.data = data
#         self.error = error


class Retry(Exception):
    def __init__(self, delay=None):
        self.delay = delay


class Fail(Exception):
    ...
