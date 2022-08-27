import pytest

from aio_services import Broker
from aio_services.brokers.nats import NatsBroker
from aio_services.brokers.kafka import KafkaBroker
from aio_services.brokers.pubsub import PubSubBroker
from aio_services.brokers.rabbitmq import RabbitmqBroker

BROKERS = [NatsBroker, KafkaBroker, PubSubBroker, RabbitmqBroker]


@pytest.mark.parametrize("broker", BROKERS)
def test_is_subclass(broker):
    assert issubclass(broker, Broker)