"""Checks over a whole recording: what no single expectation can see, in a line each."""

from pathlib import Path

import yaml

from busproof import Bus, LineContract, Machine, Signal
from machines import PackagingLine, State


async def switch_fault(unit: Machine, fault: str | None) -> None:
    """Switch a fault of the simulation on or off (demo/plant/FAULTS.md). Its topic is in no
    contract, because a real machine has no such handle."""
    await unit.bus.send(f"{unit.state.topic}/fault", {"fault": fault})


def value_of(signal: Signal) -> int:
    """The last value a signal reported, for a sum over a line that has come to rest."""
    latest = signal.latest()
    assert latest is not None, f"{signal.name} never reported"
    assert isinstance(latest.value, int)
    return latest.value


def accounted_for(line: PackagingLine) -> int:
    """Every bottle the line can say something about, to compare with those filled."""
    return (
        value_of(line.capper.reject_count)
        + value_of(line.inspector.pass_count)
        + value_of(line.inspector.reject_count)
        + value_of(line.scu.in_transit)
        + value_of(line.scu.lost)
    )


def first_report_of(bus: Bus, contract: LineContract, unit: str, state: State) -> int:
    """Where in the recording `unit` first reported `state`."""
    topic = contract.topics(unit, "state").topic
    for index, message in enumerate(bus.recorder.messages()):
        value = message.value
        if message.topic == topic and isinstance(value, dict) and value.get("state") == state:
            return index
    raise AssertionError(f"{unit} never reported {state.name}")


def illegal_changes(signal: Signal, state_machine: Path) -> list[tuple[str, str]]:
    """The state changes `signal` showed that the state machine does not allow."""
    states = yaml.safe_load(state_machine.read_text())["states"]
    allowed = {
        name: {*state["commands"].values(), *([state["done"]] if "done" in state else [])}
        for name, state in states.items()
    }
    seen = [State(message.value).name.capitalize() for message in signal.fresh(since=0)]
    changes = [(a, b) for a, b in zip(seen, seen[1:], strict=False) if a != b]
    return [(a, b) for a, b in changes if b not in allowed[a]]


def went_down(signal: Signal, since: int) -> bool:
    """Whether a counter was seen going down after `since`, a place in the recording taken once the
    line runs: a reset brings a counter back to zero, and that is no fault."""
    values = [message.value for message in signal.fresh(since=since)]
    numbers = [value for value in values if isinstance(value, int)]
    return any(later < earlier for earlier, later in zip(numbers, numbers[1:], strict=False))
