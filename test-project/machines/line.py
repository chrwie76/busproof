from busproof import Bus, Line, Topics
from machines.capper import Capper
from machines.filler import Filler
from machines.inspector import Inspector
from machines.scu import Scu


class PackagingLine(Line):
    """The three machines in the order a bottle passes them, and the SCU that coordinates them.

    `state` is the consensus of the machines, as BusProof derives it; `scu.state` is what the SCU
    claims. A line command goes to the SCU, as an operator's would.
    """

    def __init__(self, bus: Bus, topics: Topics):
        self.filler = Filler(bus, topics)
        self.capper = Capper(bus, topics)
        self.inspector = Inspector(bus, topics)
        self.scu = Scu(bus, topics)
        super().__init__(bus, [self.filler, self.capper, self.inspector], name="line")

    async def send(self, command: str) -> None:
        await self.scu.send(command)

    async def reset(self) -> None:
        await self.send("Reset")

    async def start(self) -> None:
        await self.send("Start")

    async def stop(self) -> None:
        await self.send("Stop")

    async def hold(self) -> None:
        await self.send("Hold")

    async def unhold(self) -> None:
        await self.send("Unhold")

    async def abort(self) -> None:
        await self.send("Abort")

    async def clear(self) -> None:
        await self.send("Clear")
