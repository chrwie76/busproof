"""Machines and lines — the page objects of a plant.

A test project writes one class per machine, in its constructor, and names signals by what
they mean (`good_count`), never by topic. Where that signal is, `topics` says: a function from
machine and signal (or command) to an `Address`. A test writes it by hand; later the contract
and busproof.toml provide it (docs/CONCEPT.md, decision 21). So no topic convention ever sits
here.

    class Capper(Machine):
        def __init__(self, bus: Bus, topics: Topics):
            super().__init__(bus, topics, name="capper")
            self.good_count = self.signal("good_count")

A machine object holds signals and sends commands; it asserts nothing — `expect` does that in
the test, where a reader looks for it.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

from busproof.bus import Bus
from busproof.signals import Consensus, Signal


@dataclass(frozen=True)
class Address:
    """Where a signal is: its topic, and where its value sits in the payload."""

    topic: str
    path: tuple[str, ...] = ()


# topics("capper", "good_count") -> Address("acme/…/line1/capper", ("good_count",))
Topics = Callable[[str, str], Address]


class Machine:
    def __init__(self, bus: Bus, topics: Topics, name: str, states: type[Enum] | None = None):
        self.bus = bus
        self.topics = topics
        self.name = name
        # Every PackML machine has a state; `states` says what its numbers mean. A subclass may
        # replace it if its signal is named differently.
        self.state = self.signal("state", states)

    def signal(self, name: str, enum: type[Enum] | None = None) -> Signal:
        address = self.topics(self.name, name)
        return Signal(
            self.bus, address.topic, name=f"{self.name}.{name}", path=address.path, enum=enum
        )

    async def send(self, command: str, value: object = None) -> None:
        await self.bus.send(self.topics(self.name, command).topic, value)


class Line:
    """Machines that work as one. The line's state is their consensus (`busproof.Consensus`):
    `Execute` only when every machine is in `Execute`."""

    def __init__(self, bus: Bus, machines: Sequence[Machine], name: str = "line"):
        self.bus = bus
        self.name = name
        self.machines = list(machines)
        self.state = Consensus(bus, [machine.state for machine in self.machines], f"{name}.state")

    async def send(self, command: str, value: object = None) -> None:
        """Send a command to every machine, in the order the line lists them."""
        for machine in self.machines:
            await machine.send(command, value)
