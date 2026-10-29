"""Machines name their signals by meaning; where they are comes from outside, and a line sends to
all. The plant here sends one message per machine, as the demo plant does:

    acme/plant1/packaging/line1/capper -> {"state": "Execute", "good_count": 123}
"""

from busproof import Address, Line, Machine, expect
from busproof.bus import Bus
from busproof.machines import Topics

LINE = "acme/plant1/packaging/line1"
CAPPER = f"{LINE}/capper"


def topics(machine: str, signal: str) -> Address:
    if signal == "start":
        return Address(f"{LINE}/{machine}/cmd")
    return Address(f"{LINE}/{machine}", (signal,))


class Capper(Machine):
    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="capper")
        self.good_count = self.signal("good_count")

    async def start(self) -> None:
        await self.send("start")


def test_a_signal_takes_its_address_from_topics_and_its_name_from_the_machine(bus):
    good_count = Capper(bus, topics).good_count

    assert (good_count.topic, good_count.path) == (CAPPER, ("good_count",))
    assert good_count.name == "capper.good_count"


def test_every_machine_has_a_state_as_in_packml(bus):
    assert Capper(bus, topics).state.path == ("state",)


async def test_a_command_is_sent_to_the_topic_topics_gives_for_it(bus):
    await Capper(bus, topics).start()

    assert [(message.topic, message.value) for message in bus.sent] == [(f"{CAPPER}/cmd", None)]


async def test_a_machine_signal_is_read_from_the_machines_message(bus):
    capper = Capper(bus, topics)
    bus.deliver(CAPPER, {"state": "Execute", "good_count": 3})

    await expect(capper.good_count).to_be(3, within=0)
    await expect(capper.state).to_be("Execute", within=0)


async def test_a_line_sends_a_command_to_every_machine_in_its_order(bus):
    line = Line(bus, [Machine(bus, topics, "filler"), Machine(bus, topics, "capper")])

    await line.send("start", {"batch": 7})

    assert [(message.topic, message.value) for message in bus.sent] == [
        (f"{LINE}/filler/cmd", {"batch": 7}),
        (f"{LINE}/capper/cmd", {"batch": 7}),
    ]


async def test_a_line_reads_its_state_from_the_messages_of_its_machines(bus):
    line = Line(bus, [Machine(bus, topics, "filler"), Machine(bus, topics, "capper")])
    bus.deliver(f"{LINE}/filler", {"state": "Execute", "fill_level": 95.0})
    bus.deliver(CAPPER, {"state": "Execute", "good_count": 3})

    await expect(line.state).to_be("Execute", within=0)


def test_the_state_of_a_line_is_named_after_the_line(bus):
    line = Line(bus, [Machine(bus, topics, "filler")], name="line1")

    assert line.state.name == "line1.state"
