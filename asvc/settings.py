from typing import List, Optional

from pydantic import BaseSettings, Field, validator

from asvc.utils.imports import import_from_string

from .middleware import Middleware
from .types import Encoder


class Settings(BaseSettings):
    broker_class: str = Field(..., env="BROKER_CLASS")

    def get_broker_class(self):
        return import_from_string(self.broker_class)


class BrokerSettings(BaseSettings):
    description: Optional[str] = None
    middlewares: Optional[List["Middleware"]] = None
    encoder: Optional[Encoder] = Field(None, env="BROKER_ENCODER_CLASS")

    @validator("encoder", pre=True)
    def resolve_encoder(cls, v):
        if isinstance(v, str):
            v = import_from_string(v)
        return v
