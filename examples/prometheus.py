import asyncio

from asvc import Service, CloudEvent
from asvc import Middleware
from asvc.backends.nats.broker import JetStreamBroker

from asvc.middlewares import PrometheusMiddleware

broker = JetStreamBroker(url="nats://localhost:4222")

service = Service(name="example-service")


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker, service: Service):
        self.logger.info(f"After service start, running with {broker}")
        await asyncio.sleep(5)
        for i in range(1000):
            await broker.publish("test.topic", data={"counter": i})
        self.logger.info("Published event(s)")


broker.add_middleware(SendMessageMiddleware())
broker.add_middleware(PrometheusMiddleware(run_server=True))


@service.subscribe("test.topic", prefetch_count=100)
async def prometheus_consumer(message: CloudEvent):
    print(f"Received Message {message.id} with data: {message.data}")
    # sleep = random.random()
    # print(f"Sleeping for {sleep}")
    # await asyncio.sleep(sleep)
