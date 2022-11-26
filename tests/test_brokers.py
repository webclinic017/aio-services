import pytest

from aio_services.broker import Broker
from aio_services.backends.nats import NatsBroker, JetStreamBroker
from aio_services.backends.kafka import KafkaBroker
from aio_services.backends.pubsub import PubSubBroker
from aio_services.backends.rabbitmq import RabbitmqBroker

backends = [NatsBroker, JetStreamBroker, KafkaBroker, PubSubBroker, RabbitmqBroker]


@pytest.mark.parametrize("broker", backends)
def test_is_subclass(broker):
    assert issubclass(broker, Broker)
