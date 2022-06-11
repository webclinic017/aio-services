# aio-services

*Event driven micro-framework for python*

## About

The package utilizes `pydantic` as the only required dependency.
For message format Cloud Events format is used.
Service can be run as standalone processes, or included into asgi applications.

## Multiple broker support

- NATS (with JetStream)
- Redis Pub/Sub
- Kafka
- Rabbitmq

## Optional Dependencies
  - `cli` - `click` and `aiorun`
  - `fast` - `orjson` and `uvloop`

## Motivation

Python has many "work-queue" libraries and frameworks, such as:
    - Celery
    - Dramatiq
    - Huey
    - arq

However, those libraries don't provide a pub/sub pattern, useful for creating
event driven and loosely coupled systems. Furthermore, the majority of those libraries
do not support `asyncio`. This is why this project was built.