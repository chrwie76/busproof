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
    settings_topic: str
    online_topic: str
    # The parameters it takes, with their limits, from its contract.
    settings: dict[str, dict]


def read_unit(contracts: Path, name: str) -> Unit:
    """Read one machine from `contracts`. There is no fallback copy: a missing file is an error."""
    line = _load(contracts / "line.yaml")
    entry = line["machines"][name]
    contract = _load(contracts / entry["contract"])
    behaviour = _load(contracts / entry["states"])
    channels = contract["channels"]
    settings = contract["components"]["messages"]["settings"]["payload"]["properties"]

    def topic(channel: str) -> str:
        return channels[channel]["address"].format(**line["address"])

    return Unit(
        name=name,
        states=behaviour["states"],
        initial=behaviour["initial"],
        roles=behaviour["roles"],
        status_topic=topic("status"),
        command_topic=topic("command"),
        settings_topic=topic("settings"),
        online_topic=topic("online"),
        settings=settings,
    )


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())
