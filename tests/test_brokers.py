import pytest

from asvc.broker import Broker
from asvc.backends.nats import NatsBroker, JetStreamBroker
from asvc.backends.kafka import KafkaBroker
from asvc.backends.pubsub import PubSubBroker
from asvc.backends.rabbitmq import RabbitmqBroker

backends = [NatsBroker, JetStreamBroker, KafkaBroker, PubSubBroker, RabbitmqBroker]


@pytest.mark.parametrize("broker", backends)
def test_is_subclass(broker):
    assert issubclass(broker, Broker)
