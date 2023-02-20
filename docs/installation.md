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