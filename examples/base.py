import asyncio
from aio_services import Service, CloudEvent
from aio_services import Middleware
from aio_services.backends.kafka import KafkaBroker
from aio_services.backends.nats.broker import JetStreamBroker, NatsBroker
from aio_services.backends.rabbitmq import RabbitmqBroker

backends = {
    "rabbitmq": RabbitmqBroker(url="amqp://rabbitmq:rabbitmq@localhost:5672/"),
    "kafka": KafkaBroker(bootstrap_servers="localhost:9092"),
    "nats": NatsBroker(url="nats://localhost:4222"),
    "jetstream": JetStreamBroker(url="nats://localhost:4222"),
}

BROKER_TYPE = "rabbitmq"

broker = backends[BROKER_TYPE]


service = Service(name="example-service", broker=broker)


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker, service: Service):
        print(f"After service start, running with {broker}")
        await asyncio.sleep(10)
        for i in range(100):
            await service.publish("test.topic", data={"counter": i})
        print("Published event(s)")


broker.add_middleware(SendMessageMiddleware())


@service.subscribe("test.topic")
async def example_run(message: CloudEvent):
    print(f"Received Message {message.id} with data: {message.data}")
