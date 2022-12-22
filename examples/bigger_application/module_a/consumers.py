from asvc import GenericConsumer
from .messages import MyEvent


class MyConsumer(GenericConsumer):
    async def process(self, message: MyEvent):
        pass
