# aio-services
![Tests](https://github.com/RaRhAeu/aio-services/workflows/tests/badge.svg)
![Build](https://github.com/RaRhAeu/aio-services/workflows/release/badge.svg)
![Code Coverage](https://codecov.io/gh/RaRhAeu/aio-services/branch/main/graph/badge.svg)
![License](https://img.shields.io/github/license/RaRhAeu/aio-services)
![Python](https://img.shields.io/pypi/pyversions/aio-services)
![Format](https://img.shields.io/pypi/format/aio-services)
![PyPi Status](https://img.shields.io/pypi/status/aio-services)

*Event driven microservice framework for python*

---

## About

The package utilizes `pydantic` as the only required dependency.
For message format Cloud Events format is used.
Service can be run as standalone processes, or included into starlette (e.g. FastAPI) applications.

## Multiple broker support (in progress)

- Stub (in memory using `asyncio.Queue` for PoC, local development and testing)
- NATS (with JetStream)
- Redis Pub/Sub
- Kafka
- Rabbitmq
- Google Cloud PubSub

## Optional Dependencies
  - `cli` - `click` and `aiorun`
  - `uvloop`
  - broker of choice: `nats`, `kafka`, `rabbitmq`, `redis`, `pubsub`
  - custom serializer `msgpack`, `orjson`
  - `prometheus` - Metric exposure via `PrometheusMiddleware`
  - `opentelemetry`


## Motivation

Python has many "worker-queue" libraries and frameworks, such as:
    - Celery
    - Dramatiq
    - Huey
    - arq

However, those libraries don't provide a pub/sub pattern, useful for creating
event driven and loosely coupled systems. Furthermore, the majority of those libraries
do not support `asyncio`. This is why this project was born.

## Basic usage


```python

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


## Scaling

Each message is load-balanced (depending on broker) between all service instances with the same `name`.
To scale number of processes you can use containers (docker/k8s), [supervisor](http://supervisord.org/),
or web server like gunicorn.


## TODOS:

- Automatic [Async Api](https://www.asyncapi.com/) docs generation from service definition.
- More tests
  - Integration tests with docker-compose and all backends
- [OpenTelemetry](https://opentelemetry.io/) Middleware
- More backends (zeromq, pulsar, solace?)
- Pluggable logger interface (for third party integrations)
- Docs + tutorials