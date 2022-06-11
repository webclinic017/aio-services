from aio_services.middleware import Middleware


class RetryMiddleware(Middleware):
    async def before_process_message(self, broker, message):
        ...

    async def after_process_message(self, broker, message, exc=None):
        if exc is not None:
            await message.retry()
