from asvc import Service
from .messages import MyEvent
from .consumers import MyConsumer

service_a = Service(name="service_a")

service_a.subscribe("test.topic")(MyConsumer)


@service_a.subscribe("test.topic")
async def subscriber_a(message: MyEvent):
    ...
