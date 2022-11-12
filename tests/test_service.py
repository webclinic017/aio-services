import asyncio

from aio_services import Service, CloudEvent
from aio_services.brokers.stub import StubBroker


def test_service(service):
    assert isinstance(service, Service)
    assert isinstance(service.broker, StubBroker)
    assert service.name == "test_service"


async def test_service_scope(running_service: Service, ce):
    await running_service.publish_event(ce)
    queue: asyncio.Queue = running_service.broker.topics[ce.topic]
    msg = await queue.get()
    queue.task_done()
    decoded = running_service.broker.encoder.decode(msg.data)
    ce2 = CloudEvent.parse_obj(decoded)
    assert ce.dict() == ce2.dict()
