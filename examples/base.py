import asyncio
from asvc import Service, CloudEvent
from asvc import Middleware
from asvc.backends.stub import StubBroker

broker = StubBroker()

service = Service(name="example-service", broker=broker)


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker, service: Service):
        print(f"After service start, running with {broker}")
        await asyncio.sleep(5)
        for i in range(100):
            await service.publish("test.topic", data={"counter": i})
        print("Published event(s)")


broker.add_middleware(SendMessageMiddleware())


@service.subscribe("test.topic")
async def example_run(message: CloudEvent):
    print(f"Received Message {message.id} with data: {message.data}")
