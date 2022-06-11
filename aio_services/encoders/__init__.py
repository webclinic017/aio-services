from aio_services.types import Encoder


def get_default_encoder() -> Encoder:
    try:
        from aio_services.encoders.orjson import OrjsonEncoder

        return OrjsonEncoder()
    except ImportError:
        from aio_services.encoders.json import JsonEncoder

        return JsonEncoder()
