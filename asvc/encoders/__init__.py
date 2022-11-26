from asvc.types import Encoder


def get_default_encoder() -> Encoder:
    try:
        from asvc.encoders.orjson import OrjsonEncoder

        return OrjsonEncoder()
    except ImportError:
        from asvc.encoders.json import JsonEncoder

        return JsonEncoder()
