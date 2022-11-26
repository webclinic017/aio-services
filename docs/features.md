## Aio services features

- Modern, `asyncio` based python 3.7+ syntax
- Minimal dependencies, only `pydantic` and `async_timeout` are required
- Highly scalable: each service can process hundreds of tasks concurrently,
    all messages are load balanced between all instances
- Customizable & pluggable encoders (json, msgpack, custom)
- Pluggable broker of choice:
  - Nats (with Jetstream extension)
  - Rabbitmq
  - Kafka
  - Google Cloud PubSub
  - Redis (in progress)
  - Stub - in memory broker for testing
- Easily extensible via Middlewares
- Cloud Events standard as base message structure
- 