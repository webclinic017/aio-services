from aio_services.brokers.nats import JetStreamBroker
from aio_services import Service, CloudCommand
from aio_services import Middleware

broker = JetStreamBroker(url="nats://localhost:4222")

service = Service(name="example-service", broker=broker)


class ExampleCommand(CloudCommand, topic="commands.example.run"):
    data: str


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker: JetStreamBroker, service: Service):
        cmd = ExampleCommand(
            data="Test data", topic=ExampleCommand.t, type="ExampleCommand"
        )  # TODO: FIX auto topic and type
        print(f"Sending {cmd.id}")
        await service.publish(cmd)


broker.add_middleware(SendMessageMiddleware())


@service.subscribe(ExampleCommand.t)
async def example_run(message: ExampleCommand):
    print(f"Received {message.id} with data: {message.data}")
