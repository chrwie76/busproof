"""Machines name their signals by meaning; the topics come from outside, and a line sends to all."""

from busproof import Line, Machine, expect
from busproof.bus import Bus
from busproof.machines import Topics


def topics(machine: str, signal: str) -> str:
    return f"acme/line1/{machine}/{signal}"


class Capper(Machine):
    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="capper")
        self.good_count = self.signal("good_count")

    async def start(self) -> None:
        await self.send("start")


def test_a_signal_takes_its_topic_from_topics_and_its_name_from_the_machine(bus):
    capper = Capper(bus, topics)

    assert capper.good_count.topic == "acme/line1/capper/good_count"
    assert capper.good_count.name == "capper.good_count"


def test_every_machine_has_a_state_as_in_packml(bus):
    assert Capper(bus, topics).state.topic == "acme/line1/capper/state"


async def test_a_command_is_sent_to_the_topic_topics_gives_for_it(bus):
    await Capper(bus, topics).start()

    assert [(message.topic, message.value) for message in bus.sent] == [
        ("acme/line1/capper/start", None)
    ]


async def test_a_machine_signal_can_be_expected_like_any_other(bus):
    capper = Capper(bus, topics)
    bus.deliver("acme/line1/capper/good_count", 3)

    await expect(capper.good_count).to_be(3, within=0)


async def test_a_line_sends_a_command_to_every_machine_in_its_order(bus):
    line = Line(bus, [Machine(bus, topics, "filler"), Machine(bus, topics, "capper")])

    await line.send("start", {"batch": 7})

    assert [(message.topic, message.value) for message in bus.sent] == [
        ("acme/line1/filler/start", {"batch": 7}),
        ("acme/line1/capper/start", {"batch": 7}),
    ]


def test_the_state_of_a_line_is_named_after_the_line(bus):
    line = Line(bus, [Machine(bus, topics, "filler")], name="line1")

    assert line.state.name == "line1.state"
