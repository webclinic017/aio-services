from aio_services import GenericConsumer, CloudEvent


class MyConsumer(GenericConsumer):
    name = "example_consumer"

    async def process(self, message: CloudEvent):
        print(f"Received {message}")
