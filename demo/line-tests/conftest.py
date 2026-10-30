"""The fixtures of this plant, in layers: `bus` (from BusProof) → `line` → `running_line`.

The plant keeps its state between tests, so each precondition starts by bringing it to a known
state, whatever the last test left. A test can ask for another start with
`@pytest.mark.scenario("name")`; then the units restart, while the broker and `bus` stay.
"""

import os
import subprocess
from pathlib import Path

import pytest

from busproof import Bus, LineContract, expect
from checks import switch_fault
from machines import Capper, Filler, Inspector, PackagingLine, Scu, State

WITHIN = 10  # seconds a precondition may take
COMPOSE = Path(__file__).parent.parent / "compose.yaml"
DEFAULT = "default"
UNITS = ["filler", "capper", "inspector", "scu"]

_running = {"scenario": DEFAULT}


@pytest.fixture
def scenario(request: pytest.FixtureRequest) -> str:
    """Start the plant the way this test asks. A scenario always starts fresh, as its supplies and
    counters are the point; the default needs a restart only after a scenario."""
    marker = request.node.get_closest_marker("scenario")
    wanted = marker.args[0] if marker else DEFAULT
    if wanted != DEFAULT or _running["scenario"] != DEFAULT:
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE), "up", "-d", "--force-recreate", "--no-deps"]
            + UNITS,
            env=os.environ | {"PLANT_SCENARIO": wanted},
            check=True,
            capture_output=True,
        )
        _running["scenario"] = wanted
    return wanted


async def until_listening(*units: Filler | Capper | Inspector | Scu) -> None:
    """A unit says it is online only once it listens, so a command sent now cannot get lost."""
    for unit in units:
        await expect(unit.online).to_be(True, within=WITHIN)


@pytest.fixture
async def line(scenario: str, bus: Bus, contract: LineContract) -> PackagingLine:
    """Precondition: the whole line in Stopped, with no fault on. With no scenario asked for, it is
    also full, with its parameters as they should be."""
    line = PackagingLine(bus, contract.topics)
    units = [line.filler, line.capper, line.inspector, line.scu]
    await until_listening(*units)
    for unit in units:
        await switch_fault(unit, None)
    await line.abort()  # the one command that works from nearly anywhere
    await expect(line.scu.state).to_be(State.ABORTED, within=WITHIN)
    await line.clear()
    await expect(line.scu.state).to_be(State.STOPPED, within=WITHIN)
    await expect(line.state).to_be(State.STOPPED, within=WITHIN)
    if scenario == DEFAULT:
        await line.filler.set(speed=60.0, fill_target=98.0, bottle_supply=10000, tank_level=100.0)
        await line.capper.set(torque_target=2.0, cap_supply=10000)
        await line.inspector.set(min_fill_level=90.0)
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
    await until_listening(capper)
    await switch_fault(capper, None)
    await capper.send("Abort")
    await expect(capper.state).to_be(State.ABORTED, within=WITHIN)
    await capper.send("Clear")
    await expect(capper.state).to_be(State.STOPPED, within=WITHIN)
    await capper.set(torque_target=2.0, cap_supply=10000)
    return capper


@pytest.fixture
def state_machine(settings) -> Path:
    return settings.line.parent / "packml.yaml"
