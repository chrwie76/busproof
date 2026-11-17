"""The fake bus behaves like a real one, as far as the recorder can tell."""

from busproof.bus import Bus
from busproof.fake import FakeBus


def test_a_delivered_message_is_recorded_as_received():
    bus = FakeBus()

    bus.deliver("line/capper/state", "Execute")

    message = bus.recorder.latest("line/capper/state")
    assert message is not None
    assert (message.value, message.direction) == ("Execute", "received")


async def test_a_sent_message_is_recorded_as_sent():
    bus = FakeBus()

    await bus.send("line/capper/cmd", "start")

    assert [(message.topic, message.value) for message in bus.sent] == [
        ("line/capper/cmd", "start")
    ]
    assert bus.recorder.messages()[0].direction == "sent"


async def test_received_and_sent_share_one_timeline():
    bus = FakeBus()

    await bus.send("line/capper/cmd", "start")
    bus.deliver("line/capper/state", "Starting")

    assert [message.direction for message in bus.recorder.messages()] == ["sent", "received"]


def test_the_fake_bus_is_a_bus():
    # Checked by pyright: if FakeBus stops matching the Bus interface, this line turns red.
    bus: Bus = FakeBus()
    assert bus.recorder is not None
