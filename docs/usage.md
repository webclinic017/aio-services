## Intro


## Basic Usage

```Python
import asyncio
from asvc import Service, Middleware, CloudEvent
from asvc.backends.nats import JetStreamBroker


broker = JetStreamBroker(url="nats://localhost:4222")

service = Service(name="example-service", broker=broker)


class SendMessageMiddleware(Middleware):
    async def after_service_start(self, broker: JetStreamBroker, service: Service):
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
from asvc import Service, CloudEvent
from asvc.middlewares import HealthCheckMiddleware
from asvc.backends.nats import JetStreamBroker, NatsJetStreamResultMiddleware
from asvc.web import include_service


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
        from asvc.backends.stub import StubBroker
        return StubBroker()
    else:
        from asvc.backends.rabbitmq import RabbitmqBroker
        return RabbitmqBroker(**kwargs)

broker = get_broker()

```

Furthermore, subscribers are just regular python coroutines, so it's possible to test
them simply by invocation

```python

# main.py
@service.subscribe(...)
async def my_subscriber(message: CloudEvent):
    return 42

# tests.py
from main import my_subscriber

async def test_my_subscriber():
    result = await my_subscriber(None)
    assert result == 42

```

## Configuration

*Explicit is better than implicit.*

Aio Services package does not provide any 'magic' configuration management
or dependency injection providers. You have to create `broker`, `service`, and `middlewares`
instances by hand and provide all the parameters. However, it's up to user which approach
to use: config file (yaml/ini), pydantic settings management, constants in code, dependency
injector library etc.