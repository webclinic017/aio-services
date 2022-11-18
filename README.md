# aio-services

*Event driven micro-framework for python*

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

## Scaling

Each message is load-balanced (depending on broker) between all service instances with the same `name`.
To scale number of processes you can use containers (docker/k8s), [supervisor](http://supervisord.org/),
or web server like gunicorn.


## TODOS:

- Automatic [Async Api](https://www.asyncapi.com/) docs generation from service definition.
- More tests
  - Integration tests with docker-compose and all brokers
- [OpenTelemetry](https://opentelemetry.io/) Middleware
- More brokers (zeromq, pulsar, solace?)
- Pluggable logger interface (for third party integrations)
- Docs + tutorials