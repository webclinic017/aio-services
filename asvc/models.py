from datetime import datetime
from typing import Any, Generic, Optional

from pydantic import BaseModel as _BaseModel
from pydantic import Extra, Field
from pydantic.fields import ModelField, PrivateAttr

from .types import RawMessage, T
from .utils import str_uuid
from .utils.datetime import utc_now


class BaseModel(_BaseModel):
    def dict(self, **kwargs):
        kwargs.setdefault("exclude_unset", True)
        kwargs.setdefault("by_alias", True)
        return super().dict(**kwargs)

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class CloudEvent(BaseModel, Generic[T, RawMessage]):
    version: Optional[str] = "1.0"
    content_type: str = Field("application/json", alias="datacontenttype")
    id: str = Field(default_factory=str_uuid)
    trace_id: str = Field(default_factory=str_uuid, alias="traceid")
    time: datetime = Field(default_factory=utc_now)

    topic: str = Field(..., alias="subject")
    type: Optional[str] = None
    source: Optional[str] = None
    data: Optional[Any] = None

    _raw: Optional[RawMessage] = PrivateAttr()

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

    @property
    def raw(self) -> RawMessage:
        if self._raw is None:
            raise AttributeError("raw property accessible only for incoming messages")
        return self._raw

    class Config:
        extra = Extra.allow


class PublishInfo(BaseModel):
    topic: str
    event_type: type[CloudEvent]
    kwargs: dict[str, Any]
