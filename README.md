# aio-services

*Event driven micro-framework for python*

## About

The package utilizes `pydantic` as the only required dependency.
For message format Cloud Events format is used.
Service can be run as standalone processes, or included into starlette (e.g. FastAPI) applications.

## Multiple broker support (in progress)

- Stub (in memory using `asyncio.Queue` for testing)
- NATS (with JetStream)
- Redis Pub/Sub
- Kafka
- Rabbitmq
- Google Cloud PubSub
- ZeroMQ (?)

## Optional Dependencies
  - `cli` - `click` and `aiorun`
  - `fast` - `orjson` and `uvloop`
  - broker of choice ()
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