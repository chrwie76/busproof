"""A bus over MQTT — the real thing, behind the same seam as `FakeBus`.

    async with MqttBus("mqtt://localhost:1883", listen="acme/plant1/packaging/line1/#") as bus:
        ...

It listens to the whole line, not only to the topics a test names: a message on a topic the
contract does not know is a finding, and the recorder keeps it. For the same reason a payload
that is not JSON is kept as it came, not dropped. What the bus sends is recorded as sent — and,
with MQTT 5's "no local", not heard back as if the plant had said it.

Needs the `mqtt` extra: `pip install "busproof[mqtt]"`.
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack, suppress
from urllib.parse import urlsplit

try:
    import aiomqtt
    from paho.mqtt.subscribeoptions import SubscribeOptions
except ImportError as error:
    raise ImportError('busproof.mqtt needs the mqtt extra: pip install "busproof[mqtt]"') from error

from busproof.message import Message
from busproof.recorder import Recorder


class BrokerUnreachable(ConnectionError):
    """The broker could not be reached — said in one line, with where it was looked for."""


class MqttBus:
    def __init__(self, url: str, listen: str, recorder: Recorder | None = None):
        self.recorder = recorder or Recorder()
        self.host, self.port = broker(url)
        self.listen = listen
        self._client: aiomqtt.Client | None = None
        self._stack = AsyncExitStack()
        self._reader: asyncio.Task[None] | None = None

    async def __aenter__(self) -> "MqttBus":
        username, password = credentials()
        client = aiomqtt.Client(
            self.host,
            self.port,
            username=username,
            password=password,
            protocol=aiomqtt.ProtocolVersion.V5,
        )
        try:
            await self._stack.enter_async_context(client)
        except (aiomqtt.MqttError, OSError) as error:
            raise BrokerUnreachable(
                f"cannot reach the MQTT broker at {self.host}:{self.port} — {error}"
            ) from error
        await client.subscribe(self.listen, options=SubscribeOptions(qos=1, noLocal=True))
        self._client = client
        self._reader = asyncio.create_task(self._read(client))
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._reader is not None:
            self._reader.cancel()
            with suppress(asyncio.CancelledError):
                await self._reader
        self._client = None
        await self._stack.aclose()

    async def send(self, topic: str, value: object) -> None:
        if self._client is None:
            raise RuntimeError("not connected: use `async with MqttBus(...) as bus`")
        # Recorded first, so an answer that comes back fast can never stand before its cause.
        self.recorder.record(topic, value, direction="sent")
        await self._client.publish(topic, json.dumps(value), qos=1)

    def arrived(self, topic: str, payload: object) -> Message:
        """Record a message from the broker — what the reading task does with each one."""
        return self.recorder.record(topic, decode(payload))

    async def _read(self, client: aiomqtt.Client) -> None:
        async for message in client.messages:
            self.arrived(str(message.topic), message.payload)


def decode(payload: object) -> object:
    """JSON if it is JSON; otherwise kept as it came. A message that breaks the contract is a
    finding, not noise — so it stays in the evidence, where a signal simply finds no field."""
    if isinstance(payload, bytes | bytearray):
        try:
            payload = bytes(payload).decode("utf-8")
        except UnicodeDecodeError:
            return bytes(payload)
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload
    return payload


def broker(url: str) -> tuple[str, int]:
    """Host and port from `mqtt://host:port`, as BUSPROOF_MQTT_URL gives it."""
    parts = urlsplit(url)
    if parts.scheme != "mqtt":
        raise ValueError(f"{url!r}: only mqtt://host:port for now; TLS (mqtts://) comes in M2")
    return parts.hostname or "localhost", parts.port or 1883


def credentials() -> tuple[str | None, str | None]:
    """User and password, read from the environment only now, at connect time — so they never
    sit in a configuration object that is passed around or printed. No user set: anonymous."""
    username = os.environ.get("BUSPROOF_MQTT_USERNAME") or None
    if username is None:
        return None, None
    return username, os.environ.get("BUSPROOF_MQTT_PASSWORD", "")
