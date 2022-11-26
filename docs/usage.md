## Intro



## Basic Usage

```Python
import asyncio
from aio_services import Service, CloudEvent
from aio_services import Middleware
from aio_services.backends.nats.broker import JetStreamBroker


broker = JetStreamBroker(url="nats://localhost:4222")

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
```

Run with

```shell
asvc app:service
```

## Web integration (FastAPI)

```python
from typing import Any

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, Response
from aio_services import Service, CloudEvent
from aio_services.backends.nats import JetStreamBroker, NatsJetStreamResultMiddleware

from aio_services.web import include_service
from aio_services.middlewares import HealthCheckMiddleware

broker = JetStreamBroker(url="nats://localhost:4222")
kv = NatsJetStreamResultMiddleware(bucket="test")

broker.add_middleware(HealthCheckMiddleware())
broker.add_middleware(kv)

service = Service(name="example-service", broker=broker)


app = FastAPI()

include_service(app=app, service=service, add_health_endpoint=True)


@service.subscribe("events.topic", name="test_consumer", store_results=True)
async def handler(message: CloudEvent):
    print(f"Received Message {message.id} with data: {message.data}")
    return message.data


@app.post("/publish", status_code=202, response_model=CloudEvent)
async def publish_event(data: Any = Body(...)):
    event = CloudEvent(topic="events.topic", data=data)
    await service.publish_event(event)
    return event

@app.get("/{consumer}/{key}")
async def get_result(consumer: str, key: str):
    res = await kv.get(f"{consumer}:{key}")
    if res is None:
        return Response(status_code=404, content="Key not found")
    return JSONResponse(content=res)

```

## Testing

`StubBroker` class is provided as in memory replacement for running unit tests

```python
import os


def get_broker(**kwargs):
    if os.getenv('ENV') == 'TEST':
        from aio_services.backends.stub import StubBroker
        return StubBroker(**kwargs)
    else:
        from aio_services.backends.rabbitmq import RabbitmqBroker
        return RabbitmqBroker(**kwargs)

broker = get_broker()

```