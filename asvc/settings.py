from typing import List, Optional

from pydantic import BaseSettings, Field

from asvc.utils.imports import import_from_string

from .middleware import Middleware


class Settings(BaseSettings):
    broker_class: str = Field(..., env="BROKER_CLASS")

    def get_broker_class(self):
        return import_from_string(self.broker_class)


class BrokerSettings(BaseSettings):
    description: Optional[str] = None
    middlewares: Optional[List["Middleware"]] = None
    encoder: Optional[str] = Field(None, env="BROKER_ENCODER_CLASS")

    def get_encoder(self):
        if self.encoder:
            return import_from_string(self.encoder)
        return None
