from datetime import datetime
from typing import Union, Optional, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic.fields import ModelField

from aio_services.util import utc_now


class CloudEvent(BaseModel):
    version: str = "1.0"
    content_type: str = Field("application/json", alias="datacontenttype")
    id: Union[UUID, str] = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4, alias="traceid")
    type: str = "CloudEvent"
    source: str
    subject: str
    data: Optional[Any] = None
    time: datetime = Field(default_factory=utc_now)
    extensions: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs):
        name = kwargs.get("name") or cls.__name__
        if "abstract" not in kwargs:
            cls.__fields__["type"] = ModelField(
                name="type",
                type_=Literal[name],  # type: ignore
                default=name,
                required=False,
                class_validators=None,
                model_config=cls.__config__,
            )
