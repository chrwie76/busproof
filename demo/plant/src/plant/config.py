"""What the plant starts with: `config.json`, and on top of it what a scenario changes.

A scenario is a small file that names only what differs, so it says at a glance what it is about.
A scenario that does not exist stops the service: it must not silently run the default.
"""

import json
from pathlib import Path

DEFAULT = "default"


def load_config(path: Path, scenario: str = DEFAULT) -> dict:
    config = json.loads(path.read_text())
    if scenario != DEFAULT:
        changes = json.loads((path.parent / "scenarios" / f"{scenario}.json").read_text())
        _merge(config, changes)
    return config


def _merge(config: dict, changes: dict) -> None:
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            _merge(config[key], value)
        else:
            config[key] = value
