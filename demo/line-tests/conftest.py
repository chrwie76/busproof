"""The fixtures of this plant, in layers: `bus` (from BusProof) → `line` → `running_line`."""

import asyncio
from collections.abc import AsyncIterator

import pytest

from busproof import Bus, FakeBus, LineContract, expect
from machines import Capper, PackagingLine, State
from stand_in import run_stand_in


@pytest.fixture(autouse=True)
async def stand_in(bus: Bus, contract: LineContract, settings) -> AsyncIterator[None]:
    """Without a broker there is no plant: something must answer. Does nothing on a real bus."""
    if not isinstance(bus, FakeBus):
        yield
        return
    task = asyncio.create_task(run_stand_in(bus, contract, settings.line))
    yield
    task.cancel()


@pytest.fixture
def line(bus: Bus, contract: LineContract) -> PackagingLine:
    return PackagingLine(bus, contract.topics)


@pytest.fixture
async def idle_line(line: PackagingLine) -> PackagingLine:
    """Precondition: every machine in Idle."""
    await line.reset()
    await expect(line.state).to_be(State.IDLE, within=5)
    return line


@pytest.fixture
async def running_line(idle_line: PackagingLine) -> PackagingLine:
    """Precondition: every machine in Execute."""
    await idle_line.start()
    await expect(idle_line.state).to_be(State.EXECUTE, within=5)
    return idle_line


@pytest.fixture
async def stopped_capper(bus: Bus, contract: LineContract) -> Capper:
    """Precondition: the capper alone, in Stopped — from whatever state an earlier test left."""
    capper = Capper(bus, contract.topics)
    await capper.send("Abort")  # the one command that works from nearly anywhere
    await expect(capper.state).to_be(State.ABORTED, within=5)
    await capper.send("Clear")
    await expect(capper.state).to_be(State.STOPPED, within=5)
    return capper
