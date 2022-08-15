from datetime import datetime
from typing import Any, ClassVar, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Extra, Field
from pydantic.fields import ModelField

from aio_services.utils.datetime import utc_now


class BaseConsumerOptions(BaseModel):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class BaseCloudEvent(BaseModel):
    version: Literal["1.0"] = "1.0"
    content_type: str = Field("application/json", alias="datacontenttype")
    id: Union[UUID, str] = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4, alias="traceid")
    type: str = "CloudEvent"
    source: Optional[str] = None
    topic: Optional[str] = None
    data: Optional[Any] = None
    time: datetime = Field(default_factory=utc_now)

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

    class Config:
        extra = Extra.allow
        use_enum_values = True
        allow_population_by_field_name = True


class TopicGetter:
    def __get__(self, instance, owner: BaseCloudEvent):
        return owner.__fields__["topic"].get_default()


class CloudEvent(BaseCloudEvent):
    topic: str = Field(..., alias="subject")


class CloudCommand(CloudEvent):
    t: ClassVar[TopicGetter] = TopicGetter()

    def __init_subclass__(cls, **kwargs):
        topic = kwargs.get("topic")
        if topic:
            assert isinstance(topic, str), "Topic must be string"
            cls.__fields__["topic"] = ModelField(
                name="topic",
                type_=Literal[topic],  # type: ignore
                required=False,
                default=topic,
                alias="subject",
                class_validators=None,
                model_config=cls.__config__,
            )
        else:
            raise ValueError("CloudCommand subclass must define 'topic' as class kwarg")
