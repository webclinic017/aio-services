import asyncio
from datetime import date

import pytest
import pytest_asyncio

from asvc import Service, CloudEvent, GenericConsumer, ServiceRunner
from asvc.backends.stub import StubBroker
from asvc.middleware import Middleware


@pytest_asyncio.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def middleware():
    class EmptyMiddleware(Middleware):
        pass

    return EmptyMiddleware()


@pytest.fixture
def broker(middleware):
    return StubBroker(middlewares=[middleware])


@pytest.fixture
def service(broker):
    return Service(name="test_service")


@pytest.fixture
def service_runner(service, broker):
    runner = ServiceRunner(broker=broker)
    runner.add_service(service)
    return runner


@pytest.fixture(scope="session")
def handler():
    async def example_handler(message: CloudEvent) -> int:
        assert isinstance(message, CloudEvent)
        return 42

    return example_handler


@pytest.fixture()
def test_consumer(service, handler):
    consumer_name = "test_consumer"
    service.subscribe("test_topic", name=consumer_name)(handler)
    return service.consumers[consumer_name]


@pytest.fixture()
def generic_test_consumer(service):
    class TestConsumer(GenericConsumer):
        name = "test_generic_consumer"

        async def process(self, message: CloudEvent):
            assert isinstance(message, CloudEvent)
            return 42

    service.subscribe("test_topic")(TestConsumer)


@pytest.fixture()
def ce() -> CloudEvent:
    return CloudEvent(
        type="TestEvent",
        topic="test_topic",
        data={"today": date.today().isoformat(), "arr": [1, "2", 3.0]},
    )


@pytest_asyncio.fixture()
async def running_service(runner: ServiceRunner) -> None:
    await runner.start()
    yield
    await runner.stop()
