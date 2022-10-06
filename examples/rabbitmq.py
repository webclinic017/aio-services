from aio_services.brokers.rabbitmq import RabbitmqBroker
from aio_services import Service, CloudCommand

broker = RabbitmqBroker(url="nats://localhost:4222")

service = Service(name="example-service", broker=broker)


class ExampleCommand(CloudCommand, topic="commands.example.run"):
    data: str


@service.subscribe(ExampleCommand.t)
async def example_run(message: ExampleCommand):
    print(f"Received {message.id} with data: {message.data}")
