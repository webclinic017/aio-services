import pytest

from aio_services import CloudEvent
from aio_services.encoders.json import JsonEncoder
from aio_services.encoders.orjson import OrjsonEncoder
from aio_services.encoders.pickle import PickleEncoder
from aio_services.encoders.msgpack import MsgPackEncoder


@pytest.mark.parametrize(
    "encoder", (JsonEncoder, OrjsonEncoder, PickleEncoder, MsgPackEncoder)
)
@pytest.mark.parametrize("data", (1, "2", 3.0, [None], {"key": "value", "1": 2}))
def test_encoders_simple_data(encoder, data):
    encoded = encoder.encode(data)
    assert isinstance(encoded, bytes)
    decoded = encoder.decode(encoded)
    assert decoded == data


@pytest.mark.parametrize(
    "encoder", (JsonEncoder, OrjsonEncoder, PickleEncoder, MsgPackEncoder)
)
@pytest.mark.parametrize("data", (1, "2", 3.0, [None], {"key": "value", "1": 2}))
def test_encoder_cloud_events(encoder, data):
    ce = CloudEvent(topic="test.topic", data=data, type="TestEvent")
    ce_dict = ce.dict()
    encoded = encoder.encode(ce_dict)
    assert isinstance(encoded, bytes)
    decoded = encoder.decode(encoded)
    assert decoded["data"] == ce_dict["data"]
