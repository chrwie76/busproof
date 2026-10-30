"""What a unit of the plant reads from the mounted contracts: where it stands, what it may do."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Unit:
    name: str
    # The state machine: states with their numbers, commands and where acting states lead.
    states: dict[str, dict]
    initial: str
    # What a state means, so no state name is written in the code.
    roles: dict[str, list[str]]
    status_topic: str
    command_topic: str
    online_topic: str
    # The parameters it takes, with their limits, from its contract. The SCU takes none.
    settings_topic: str | None
    settings: dict[str, dict]


@dataclass(frozen=True)
class Plan:
    """What the SCU needs to know of the line: its machines, and what it should do with them."""

    machines: dict[str, Unit]
    start_order: list[str]
    stop_order: list[str]
    on_machine_fault: str


def read_unit(contracts: Path, name: str) -> Unit:
    """Read one unit from `contracts`. There is no fallback copy: a missing file is an error."""
    line = _load(contracts / "line.yaml")
    controller = line["controller"]
    entry = controller if name == controller["name"] else line["machines"][name]
    contract = _load(contracts / entry["contract"])
    behaviour = _load(contracts / entry["states"])
    channels = contract["channels"]
    messages = contract["components"]["messages"]

    def topic(channel: str) -> str:
        return channels[channel]["address"].format(**line["address"])

    return Unit(
        name=name,
        states=behaviour["states"],
        initial=behaviour["initial"],
        roles=behaviour["roles"],
        status_topic=topic("status"),
        command_topic=topic("command"),
        online_topic=topic("online"),
        settings_topic=topic("settings") if "settings" in channels else None,
        settings=messages["settings"]["payload"]["properties"] if "settings" in messages else {},
    )


def read_plan(contracts: Path) -> Plan:
    line = _load(contracts / "line.yaml")
    controller = line["controller"]
    return Plan(
        machines={name: read_unit(contracts, name) for name in line["machines"]},
        start_order=controller["start_order"],
        stop_order=controller["stop_order"],
        on_machine_fault=controller["on_machine_fault"],
    )


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())
