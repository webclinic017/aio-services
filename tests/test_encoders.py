import pytest

from aio_services.encoders.json import JsonEncoder
from aio_services.encoders.orjson import OrjsonEncoder


@pytest.mark.parametrize("encoder", (JsonEncoder, OrjsonEncoder))
@pytest.mark.parametrize("data", (1, "2", 3.0, [None], {"key": "value", "1": 2}))
def test_encoders(encoder, data):
    encoded = encoder.encode(data)
    assert isinstance(encoded, bytes)
    decoded = encoder.decode(encoded)
    assert decoded == data
