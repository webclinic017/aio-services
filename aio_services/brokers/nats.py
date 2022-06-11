import functools
from typing import Optional, Type, Callable, Awaitable

import nats
from nats.aio.msg import Msg as NatsMsg
from nats.js import JetStreamContext

from aio_services.broker import Broker, Consumer, MessageProxy
from aio_services.types import DataT
from aio_services.models import CloudEvent


class NatsMessageProxy(MessageProxy[NatsMsg, DataT]):
    async def _ack(self, **kwargs):
        if not self._message._ackd:
            await self._message.ack()

    async def _nack(self, *, delay=None, **kwargs):
        return await self._message.nak(delay=delay)


NatsHandlerT = Callable[[MessageProxy[NatsMsg, DataT]], Awaitable[Optional[CloudEvent]]]


class NatsConsumer(Consumer[NatsMsg]):
    def __init__(
        self,
        group_id: str,
        topic: str,
        fn: NatsHandlerT,
        auto_ack: bool = True,
        durable: Optional[str] = None,
        max_retries=3,
        timeout=60,
        **kwargs
    ):
        super().__init__(group_id, topic, fn, auto_ack, **kwargs)
        self.durable = durable
        self.max_retries = max_retries
        self.timeout = timeout
        self.sub_opts = kwargs

    async def _consume(self, broker) -> None:
        await broker.nc.subscribe(
            "foo", cb=functools.partial(self._process_message, broker)
        )


class NatsBroker(Broker[NatsMsg]):
    def __init__(self, *, group_id: str, servers: str, **kwargs):
        super().__init__(group_id=group_id)
        self.servers = servers
        self.conn_opt = kwargs
        self._nc = None

    @property
    def nc(self) -> nats.NATS:
        assert self._nc is not None, "Broker not connected"
        return self._nc

    async def connect(self):
        self._nc = nats.connect(self.servers, **self.conn_opt)

    async def _publish(self, topic: str, message, **kwargs):
        pass

    @property
    def consumer_class(self) -> Type[NatsConsumer]:
        return NatsConsumer


class JetStreamConsumer(NatsConsumer):
    def __init__(
        self,
        group_id: str,
        topic: str,
        fn: NatsHandlerT,
        auto_ack: bool = True,
        prefetch_count: int = 10,
        **kwargs
    ):
        super().__init__(group_id, topic, fn, auto_ack, **kwargs)
        self.prefetch_count = prefetch_count

    async def _consume(self, broker: "JetStreamBroker") -> None:
        subscription = await broker.js.pull_subscribe(
            self.topic, self.group_id, **self.sub_opts
        )
        while True:
            try:
                messages = await subscription.fetch(
                    batch=self.prefetch_count, timeout=self.timeout
                )
                for message in messages:
                    # TODO: asyncio.gather(...)
                    await self._process_message(broker, message)

            except nats.errors.TimeoutError:
                pass


class JetStreamBroker(NatsBroker):
    def __init__(self, *, group_id: str, servers: str, streams=None, **kwargs):
        super().__init__(group_id=group_id, servers=servers, **kwargs)
        self.streams = streams
        self._js = None

    @property
    def js(self) -> JetStreamContext:
        assert self._js is not None, "Broker not connected"
        return self._js

    async def connect(self):
        await super().connect()
        self._js = self.nc.jetstream()

    async def _publish(self, topic: str, message: bytes, **kwargs):
        await self.js.publish(subject=topic, payload=message, **kwargs)

    @property
    def consumer_class(self) -> Type[JetStreamConsumer]:
        return JetStreamConsumer
