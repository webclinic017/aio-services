# Available Backends (Brokers)

## Base Broker

::: asvc.broker.Broker
    handler: python
    options:
        members:
            - publish
            - publish_event
        show_root_heading: true
        show_source: false
        show_bases: false


::: asvc.backends.stub.StubBroker
    handler: python
    options:
        show_root_heading: true
        show_source: false
        show_bases: false

::: asvc.backends.nats.NatsBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false


::: asvc.backends.nats.JetStreamBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false

::: asvc.backends.rabbitmq.RabbitmqBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false

::: asvc.backends.kafka.KafkaBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false

::: asvc.backends.redis.RedisBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false

::: asvc.backends.pubsub.PubSubBroker
    handler: python
    options:
      show_root_heading: true
      show_source: false
      show_bases: false

## Custom Broker

Create custom broker by subclassing `asvc.broker.Broker` and implementing abstract methods.
