"""Machines name their signals by meaning; where they are comes from outside, and a line sends to
all. The plant here sends one message per machine, as the demo plant does:

    acme/plant1/packaging/line1/capper -> {"state": "Execute", "good_count": 123}
"""

from enum import IntEnum

from busproof import Address, Line, Machine, expect
from busproof.bus import Bus
from busproof.machines import Topics

LINE = "acme/plant1/packaging/line1"
CAPPER = f"{LINE}/capper"


def topics(machine: str, name: str) -> Address:
    if name in ("Start", "Stop"):
        return Address(f"{LINE}/{machine}/cmd", ("command",))
    return Address(f"{LINE}/{machine}", (name,))


class Capper(Machine):
    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="capper")
        self.good_count = self.signal("good_count")

    async def start(self) -> None:
        await self.send("Start")


def test_a_signal_takes_its_address_from_topics_and_its_name_from_the_machine(bus):
    good_count = Capper(bus, topics).good_count

    assert (good_count.topic, good_count.path) == (CAPPER, ("good_count",))
    assert good_count.name == "capper.good_count"


def test_every_machine_has_a_state_as_in_packml(bus):
    assert Capper(bus, topics).state.path == ("state",)


async def test_a_line_of_machines_that_send_numbers_is_read_by_name(bus):
    class State(IntEnum):
        IDLE = 4
        EXECUTE = 6

    filler, capper = (Machine(bus, topics, name, states=State) for name in ("filler", "capper"))
    line = Line(bus, [filler, capper])
    bus.deliver(f"{LINE}/filler", {"state": 6})
    bus.deliver(CAPPER, {"state": 4})

    latest = line.state.latest()
    assert latest is not None
    assert repr(latest.value) == "mixed(filler.state=EXECUTE (6), capper.state=IDLE (4))"


async def test_a_command_is_sent_to_the_topic_topics_gives_for_it(bus):
    await Capper(bus, topics).start()

    assert [(message.topic, message.value) for message in bus.sent] == [
        (f"{CAPPER}/cmd", {"command": "Start"})
    ]


async def test_a_command_without_a_path_is_sent_as_its_bare_name(bus):
    await Machine(bus, lambda machine, name: Address(f"{LINE}/{machine}/{name}"), "capper").send(
        "Stop"
    )

    assert [(message.topic, message.value) for message in bus.sent] == [(f"{CAPPER}/Stop", "Stop")]


async def test_parameters_for_one_topic_travel_in_one_message(bus):
    def parameters(machine: str, name: str) -> Address:
        return Address(f"{LINE}/{machine}/set", (name.removeprefix("set "),))

    await Machine(bus, parameters, "capper").set(speed=60, torque=2.0)

    assert [(message.topic, message.value) for message in bus.sent] == [
        (f"{CAPPER}/set", {"speed": 60, "torque": 2.0})
    ]


async def test_a_machine_signal_is_read_from_the_machines_message(bus):
    capper = Capper(bus, topics)
    bus.deliver(CAPPER, {"state": "Execute", "good_count": 3})

    await expect(capper.good_count).to_be(3, within=0)
    await expect(capper.state).to_be("Execute", within=0)


async def test_a_line_sends_a_command_to_every_machine_in_its_order(bus):
    line = Line(bus, [Machine(bus, topics, "filler"), Machine(bus, topics, "capper")])

    await line.send("Stop")

    assert [(message.topic, message.value) for message in bus.sent] == [
        (f"{LINE}/filler/cmd", {"command": "Stop"}),
        (f"{LINE}/capper/cmd", {"command": "Stop"}),
    ]


async def test_a_line_reads_its_state_from_the_messages_of_its_machines(bus):
    line = Line(bus, [Machine(bus, topics, "filler"), Machine(bus, topics, "capper")])
    bus.deliver(f"{LINE}/filler", {"state": "Execute", "fill_level": 95.0})
    bus.deliver(CAPPER, {"state": "Execute", "good_count": 3})

    await expect(line.state).to_be("Execute", within=0)


def test_the_state_of_a_line_is_named_after_the_line(bus):
    line = Line(bus, [Machine(bus, topics, "filler")], name="line1")

    assert line.state.name == "line1.state"
