from busproof import Bus, Line, Topics
from machines.capper import Capper
from machines.filler import Filler
from machines.inspector import Inspector


class PackagingLine(Line):
    """The three machines in the order a bottle passes them. `state` is their consensus."""

    def __init__(self, bus: Bus, topics: Topics):
        self.filler = Filler(bus, topics)
        self.capper = Capper(bus, topics)
        self.inspector = Inspector(bus, topics)
        super().__init__(bus, [self.filler, self.capper, self.inspector], name="line")

    async def reset(self) -> None:
        await self.send("Reset")

    async def start(self) -> None:
        await self.send("Start")

    async def stop(self) -> None:
        await self.send("Stop")

    async def hold(self) -> None:
        await self.send("Hold")
