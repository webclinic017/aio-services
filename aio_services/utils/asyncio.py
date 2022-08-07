import asyncio
import functools


def run_async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return wrapper


def backoff(max_retries: int = 3):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    return await func(*args, **kwargs)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    if attempt >= max_retries:
                        raise
                    attempt += 1
                    await asyncio.sleep(attempt**2)

        return wrapped

    return wrapper
