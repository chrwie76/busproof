"""The one place the plant touches a bus. Another protocol would replace this file only."""

import asyncio
import json
import logging
from urllib.parse import urlsplit

import aiomqtt

from plant.machine import Machine

logger = logging.getLogger("plant")
RETRY_SECONDS = 1.0


async def serve(machine: Machine, url: str, tick_seconds: float, report_seconds: float) -> None:
    """Keep the machine on the broker, and reconnect when the broker goes away."""
    parts = urlsplit(url)
    unit = machine.unit
    # The broker says this for the machine when the machine can no longer say anything.
    will = aiomqtt.Will(unit.online_topic, json.dumps({"online": False}), qos=1, retain=True)
    while True:
        try:
            async with aiomqtt.Client(
                parts.hostname or "localhost", parts.port or 1883, will=will
            ) as client:
                await client.publish(unit.online_topic, json.dumps({"online": True}), 1, True)
                for topic in machine.listens_to():
                    await client.subscribe(topic, qos=1)
                logger.info("%s on %s, reporting to %s", unit.name, url, unit.status_topic)
                async with asyncio.TaskGroup() as tasks:
                    tasks.create_task(_listen(machine, client))
                    tasks.create_task(_run(machine, client, tick_seconds, report_seconds))
        except* (aiomqtt.MqttError, OSError) as errors:
            logger.warning("no broker at %s (%s); trying again", url, errors.exceptions[0])
            await asyncio.sleep(RETRY_SECONDS)


async def _listen(machine: Machine, client: aiomqtt.Client) -> None:
    async for message in client.messages:
        receive(machine, str(message.topic), message.payload)


def receive(machine: Machine, topic: str, payload: object) -> None:
    """Act on one message. Whatever makes no sense is logged and changes nothing."""
    try:
        if not isinstance(payload, str | bytes | bytearray):
            raise ValueError("no payload")
        machine.hear(topic, json.loads(payload))
    except (TypeError, ValueError, KeyError) as error:
        logger.warning("ignored a message on %s: %r", topic, error)


async def _run(
    machine: Machine, client: aiomqtt.Client, tick_seconds: float, report_seconds: float
) -> None:
    """Move time on; report on every change, and at a steady pace when nothing changes."""
    last: dict[str, object] | None = None
    since_report = report_seconds
    while True:
        machine.tick(tick_seconds)
        for topic, message in machine.outgoing():
            await client.publish(topic, json.dumps(message), qos=1)
        report = machine.report()
        since_report += tick_seconds
        if report != last or since_report >= report_seconds:
            await client.publish(machine.unit.status_topic, json.dumps(report), qos=0)
            last, since_report = report, 0.0
        await asyncio.sleep(tick_seconds)
