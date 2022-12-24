from __future__ import annotations

import json
from collections import defaultdict
from typing import TYPE_CHECKING, Literal

from asvc.asyncapi.models import AsyncAPI, ChannelItem, Info, Message, Operation, Tag

if TYPE_CHECKING:
    from asvc import Service


def get_channels_spec(service: Service) -> dict[str, ChannelItem]:
    channels: dict[str, ChannelItem] = defaultdict(ChannelItem)
    tags = {t["name"]: Tag(**t) for t in service.tags_metadata}
    for publishes in service.publish_registry.values():
        publish = Operation(
            message=Message(
                description=publishes.kwargs.get(
                    "description", publishes.event_type.__doc__
                ),
                payload=publishes.event_type.schema(
                    ref_template="#/components/messages/{model}"
                ),
                # tags=[tags[t] for t in publishes.kwargs.get("tags", [])],
            )
        )
        channels[publishes.topic].publish = publish
    for consumer in service.consumers.values():
        subscribe = Operation(
            message=Message(
                description=consumer.description,
                tags=[tags[t] for t in consumer.options.get("tags", [])],
                payload=consumer.event_type.schema(
                    ref_template="#/components/messages/{model}"
                ),
            )
        )
        channels[consumer.topic].subscribe = subscribe
    return channels


def get_async_api_spec(service: Service) -> AsyncAPI:
    doc_model = AsyncAPI(
        info=Info(title=service.title, version=service.version),
        servers={},
        channels=get_channels_spec(service),
    )
    return doc_model


def save_async_api_to_file(
    spec: AsyncAPI, path: str, fmt: Literal["json", "yaml"]
) -> None:
    dump = json.dump
    if fmt == "yaml":
        import yaml

        dump = yaml.dump
    with open(path, "w") as f:
        dump(spec.dict(by_alias=True, exclude_none=True), f)
