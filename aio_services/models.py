from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Extra, Field
from pydantic.fields import ModelField

from aio_services.types import RawMessage
from aio_services.utils.datetime import utc_now

UUIDStr = Union[UUID, str]


class CloudEvent(BaseModel):
    version: Optional[str] = "1.0"
    content_type: str = Field("application/json", alias="datacontenttype")
    id: UUIDStr = Field(default_factory=uuid4)
    trace_id: Optional[UUIDStr] = Field(default_factory=uuid4, alias="traceid")
    topic: str = Field(..., alias="subject")
    type: Optional[str] = None
    source: Optional[str] = None
    data: Optional[Any] = None
    time: datetime = Field(default_factory=utc_now)

    _raw: Optional[RawMessage] = None

    def __init_subclass__(cls, **kwargs):
        if "abstract" not in kwargs:
            name = kwargs.get("type") or cls.__name__
            cls.__fields__["type"] = ModelField(
                name="type",
                type_=str,
                default=name,
                required=False,
                class_validators=None,
                model_config=cls.__config__,
            )

    def dict(self, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().dict(**kwargs)

    @property
    def raw(self):
        if self._raw is None:
            raise AttributeError("raw property accessible only for incoming messages")
        return self._raw

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        extra = Extra.allow
