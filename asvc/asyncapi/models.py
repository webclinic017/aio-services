from typing import Any, Optional

from pydantic import BaseModel, Field


class Info(BaseModel):
    title: str
    version: str


class Message(BaseModel):
    description: Optional[str] = None
    tags: list[str] = []
    payload: dict[str, Any]


class Operation(BaseModel):
    summary: Optional[str] = None
    message: Message


class ChannelItem(BaseModel):
    publish: Optional[Operation] = None
    subscribe: Optional[Operation] = None


class Server(BaseModel):
    url: Optional[str] = None
    protocol: str
    description: Optional[str] = None


class ExternalDocs(BaseModel):
    description: Optional[str] = None
    url: str


class Tag(BaseModel):
    name: str
    description: Optional[str] = None
    external_docs: Optional[str] = Field(None, alias="externalDocs")


class AsyncAPI(BaseModel):
    asyncapi: str = "2.5.0"
    info: Info
    servers: dict[str, Server] = {}
    channels: dict[str, ChannelItem] = {}
    default_content_type: str = Field("application/json", alias="defaultContentType")
