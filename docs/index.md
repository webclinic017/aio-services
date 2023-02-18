# Welcome to Aio Services Documentation

## Version 0.1.0

*Event driven microservice framework for python*


## Installation

```shell
pip install asvc
```
or

```shell
poetry install asvc
```

### Installing optional dependencies:

```shell
pip install asvc[extension]
```

### Available extensions:

Misc:

- `cli`
- `prometheus`

Brokers:

- `nats`
- `rabbitmq`
- `kafka`
- `pubsub`
- `redis`

Encoders:

- `orjson`
- `ormsgpack`


### Installing multiple extensions:

```shell
pip install asvc[cli, orjson, nats]
```