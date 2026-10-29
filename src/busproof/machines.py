"""Machines and lines — the page objects of a plant.

A test project writes one class per machine, in its constructor, and names signals by what
they mean (`good_count`), never by topic. Which topic that is, `topics` says: a function from
machine and signal (or command) to topic. A test writes it by hand; later the contract and
busproof.toml provide it (docs/CONCEPT.md, decision 21). So no topic convention ever sits here.

    class Capper(Machine):
        def __init__(self, bus: Bus, topics: Topics):
            super().__init__(bus, topics, name="capper")
            self.good_count = self.signal("good_count")

A machine object holds signals and sends commands; it asserts nothing — `expect` does that in
the test, where a reader looks for it.
"""

from collections.abc import Callable, Sequence

from busproof.bus import Bus
from busproof.signals import Consensus, Signal

# topics("capper", "good_count") -> "acme/line1/capper/good_count"
Topics = Callable[[str, str], str]


class Machine:
    def __init__(self, bus: Bus, topics: Topics, name: str):
        self.bus = bus
        self.topics = topics
        self.name = name
        # Every PackML machine has a state; a subclass may replace it if its signal is named
        # differently.
        self.state = self.signal("state")

    def signal(self, name: str) -> Signal:
        return Signal(self.bus, self.topics(self.name, name), name=f"{self.name}.{name}")

    async def send(self, command: str, value: object = None) -> None:
        await self.bus.send(self.topics(self.name, command), value)


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
