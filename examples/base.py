import asyncio


from aio_services import Service, CloudEvent
from aio_services import Middleware
from aio_services.brokers.kafka import KafkaBroker
from aio_services.brokers.nats.broker import JetStreamBroker
from aio_services.brokers.rabbitmq import RabbitmqBroker

BROKERS = {
    "kafka": KafkaBroker(bootstrap_servers="localhost:9092"),
    "nats": JetStreamBroker(url="nats://localhost:4222"),
    "rabbitmq": RabbitmqBroker(url="amqp://rabbitmq:rabbitmq@localhost:5672/"),
}

KEY = "rabbitmq"

broker = BROKERS[KEY]


service = Service(name="example-service", broker=broker)


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker, service: Service):
        print(f"After service start, running with {broker}")
        await asyncio.sleep(10)
        for i in range(10):
            await service.publish("test.topic", data={"counter": i}, type_="CloudEvent")
        print("Published event")


broker.add_middleware(SendMessageMiddleware())


@service.subscribe("test.topic")
async def example_run(message: CloudEvent):
    print(f"Received Message {message.id} with data: {message.data}")
