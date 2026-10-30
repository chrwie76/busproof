"""A scenario changes only what it names, cannot be misspelt, and still keeps the contract."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft7Validator

from plant.config import load_config
from plant.contracts import read_unit
from plant.machine import Machine

PLANT = Path(__file__).parents[1]
CONTRACTS = PLANT.parent / "contracts"
SCENARIOS = sorted(path.stem for path in (PLANT / "scenarios").glob("*.json"))


def test_a_scenario_changes_what_it_names_and_nothing_else():
    default = load_config(PLANT / "config.json")
    config = load_config(PLANT / "config.json", "low_caps")

    assert config["units"]["capper"]["cap_supply"] == 3
    assert config["units"]["capper"]["torque_target"] == default["units"]["capper"]["torque_target"]
    assert config["units"]["filler"] == default["units"]["filler"]


def test_a_scenario_that_does_not_exist_is_an_error_not_the_default():
    with pytest.raises(FileNotFoundError):
        load_config(PLANT / "config.json", "no_such_scenario")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_scenario_starts_every_machine_within_its_contract(scenario: str):
    config = load_config(PLANT / "config.json", scenario)

    for name in ("filler", "capper", "inspector"):
        contract = yaml.safe_load((CONTRACTS / "machines" / f"{name}.asyncapi.yaml").read_text())
        schema = Draft7Validator(contract["components"]["messages"]["status"]["payload"])
        report: Any = Machine(read_unit(CONTRACTS, name), config["units"][name], 0.5).report()
        assert not list(schema.iter_errors(report)), name
