from asvc import GenericConsumer, CloudEvent
from asvc.middlewares.consumer_setup import ConsumerSetupMiddleware, on_startup

consumer_setup_middleware = ConsumerSetupMiddleware()  # add to broker


class MyConsumer(GenericConsumer):
    name = "example_consumer"
    x: int

    @on_startup
    async def setup_consumer(self):
        self.x = 10
        self.logger.info(f"Setup consumer {self.name}")

    async def process(self, message: CloudEvent):
        print(f"Received {message}")
