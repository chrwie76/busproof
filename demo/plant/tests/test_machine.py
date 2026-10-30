"""The simulation computes right: it follows the state machine, counts, and keeps its contract."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft7Validator

from plant.capper import Capper
from plant.contracts import Unit, read_unit

CONTRACTS = Path(__file__).parents[2] / "contracts"
START: dict[str, object] = {
    "good_count": 0,
    "reject_count": 0,
    "torque": 0.0,
    "speed": 60.0,
    "torque_target": 2.0,
}
ACTING = 0.5


@pytest.fixture
def unit() -> Unit:
    return read_unit(CONTRACTS, "capper")


@pytest.fixture
def capper(unit: Unit) -> Capper:
    return Capper(unit, START, ACTING)


def bring_to_execute(capper: Capper) -> None:
    capper.take("Reset")
    capper.tick(ACTING)
    capper.take("Start")
    capper.tick(ACTING)


def test_the_unit_stands_where_the_line_says(unit: Unit):
    assert unit.status_topic == "acme/plant1/packaging/line1/capper"
    assert unit.command_topic == "acme/plant1/packaging/line1/capper/cmd"


def test_a_missing_contract_is_an_error_not_a_fallback(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_unit(tmp_path, "capper")


def test_it_starts_in_the_initial_state(capper: Capper):
    assert capper.state == "Stopped"
    assert capper.report()["state"] == 2


def test_a_command_the_state_accepts_moves_it(capper: Capper):
    assert capper.take("Reset") is True
    assert capper.state == "Resetting"


def test_a_command_the_state_does_not_accept_moves_nothing(capper: Capper):
    assert capper.take("Start") is False
    assert capper.state == "Stopped"


def test_an_acting_state_finishes_on_its_own_only_when_its_time_is_up(capper: Capper):
    capper.take("Reset")

    capper.tick(ACTING / 2)
    assert capper.state == "Resetting"

    capper.tick(ACTING / 2)
    assert capper.state == "Idle"


def test_it_counts_at_its_speed_while_producing(capper: Capper):
    bring_to_execute(capper)
    counted = capper.status["good_count"]
    assert isinstance(counted, int)

    for _ in range(100):
        capper.tick(0.1)  # 10 seconds at 60 bottles a minute

    assert capper.status["good_count"] == counted + 10


def test_it_counts_nothing_unless_producing(capper: Capper):
    capper.take("Reset")
    capper.tick(ACTING)

    for _ in range(100):
        capper.tick(0.1)

    assert capper.status["good_count"] == 0


def test_a_reset_starts_the_counters_again(capper: Capper):
    bring_to_execute(capper)
    capper.tick(5)
    capper.take("Stop")
    capper.tick(ACTING)
    capper.take("Reset")

    assert capper.status["good_count"] == 0


def test_a_parameter_within_its_limits_is_taken_and_reported(capper: Capper):
    assert capper.change({"speed": 90.0}) == ["speed"]
    assert capper.report()["speed"] == 90.0


@pytest.mark.parametrize(
    "values",
    [{"speed": 500.0}, {"speed": -1}, {"speed": "fast"}, {"speed": True}, {"good_count": 7}],
)
def test_a_parameter_outside_the_contract_is_refused(capper: Capper, values: dict):
    assert capper.change(values) == []
    assert capper.status["good_count"] == 0
    assert capper.status["speed"] == 60.0


def test_the_speed_set_decides_how_fast_it_counts(capper: Capper):
    bring_to_execute(capper)
    capper.change({"speed": 120.0})

    capper.tick(5)

    assert capper.status["good_count"] == 10


def test_every_report_keeps_the_contract_in_every_state(capper: Capper, unit: Unit):
    contract = yaml.safe_load((CONTRACTS / "machines" / "capper.asyncapi.yaml").read_text())
    schema = Draft7Validator(contract["components"]["messages"]["status"]["payload"])

    for name in unit.states:
        capper.state = name
        report: Any = capper.report()
        assert not list(schema.iter_errors(report)), name
