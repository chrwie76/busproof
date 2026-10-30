"""The fixtures of this plant, in layers: `bus` (from BusProof) → `line` → `running_line`.

The plant keeps its state between tests, so each precondition starts by bringing it to a known
state, whatever the last test left.
"""

import pytest

from busproof import Bus, LineContract, expect
from machines import Capper, PackagingLine, State

WITHIN = 10  # seconds a precondition may take


@pytest.fixture
async def line(bus: Bus, contract: LineContract) -> PackagingLine:
    """Precondition: the whole line in Stopped, the SCU and every machine."""
    line = PackagingLine(bus, contract.topics)
    await line.abort()  # the one command that works from nearly anywhere
    await expect(line.scu.state).to_be(State.ABORTED, within=WITHIN)
    await line.clear()
    await expect(line.scu.state).to_be(State.STOPPED, within=WITHIN)
    await expect(line.state).to_be(State.STOPPED, within=WITHIN)
    return line


@pytest.fixture
async def idle_line(line: PackagingLine) -> PackagingLine:
    """Precondition: every machine in Idle."""
    await line.reset()
    await expect(line.state).to_be(State.IDLE, within=WITHIN)
    await expect(line.scu.state).to_be(State.IDLE, within=WITHIN)
    return line


@pytest.fixture
async def running_line(idle_line: PackagingLine) -> PackagingLine:
    """Precondition: every machine in Execute."""
    await idle_line.start()
    await expect(idle_line.state).to_be(State.EXECUTE, within=WITHIN)
    await expect(idle_line.scu.state).to_be(State.EXECUTE, within=WITHIN)
    return idle_line


@pytest.fixture
async def stopped_capper(bus: Bus, contract: LineContract) -> Capper:
    """Precondition: the capper alone, in Stopped — from whatever state an earlier test left."""
    capper = Capper(bus, contract.topics)
    await capper.send("Abort")
    await expect(capper.state).to_be(State.ABORTED, within=WITHIN)
    await capper.send("Clear")
    await expect(capper.state).to_be(State.STOPPED, within=WITHIN)
    return capper
