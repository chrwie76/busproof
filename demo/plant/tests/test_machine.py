"""The simulation computes right: it follows the state machine, makes and judges bottles, uses up
its supplies, and keeps its contract."""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft7Validator

from plant.capper import Capper
from plant.contracts import Unit, read_unit
from plant.filler import Filler
from plant.inspector import Inspector
from plant.machine import Machine

CONTRACTS = Path(__file__).parents[2] / "contracts"
CONFIG = json.loads((Path(__file__).parents[1] / "config.json").read_text())
ACTING = 0.5
MACHINES: dict[str, type[Machine]] = {"filler": Filler, "capper": Capper, "inspector": Inspector}


def build(name: str, **changes: object) -> Machine:
    start = CONFIG["units"][name] | changes
    return MACHINES[name](read_unit(CONTRACTS, name), start, ACTING)


def bring_to_execute(machine: Machine) -> None:
    machine.take("Reset")
    machine.tick(ACTING)
    machine.take("Start")
    machine.tick(ACTING)
    machine.outgoing()


def status_schema(name: str) -> Draft7Validator:
    contract = yaml.safe_load((CONTRACTS / "machines" / f"{name}.asyncapi.yaml").read_text())
    return Draft7Validator(contract["components"]["messages"]["status"]["payload"])


# --- the state machine ---------------------------------------------------------------------------


@pytest.fixture
def capper() -> Machine:
    return build("capper")


def test_the_unit_stands_where_the_line_says():
    unit: Unit = read_unit(CONTRACTS, "capper")

    assert unit.status_topic == "acme/plant1/packaging/line1/capper"
    assert unit.command_topic == "acme/plant1/packaging/line1/capper/cmd"


def test_a_missing_contract_is_an_error_not_a_fallback(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_unit(tmp_path, "capper")


def test_it_starts_in_the_initial_state(capper: Machine):
    assert capper.state == "Stopped"
    assert capper.report()["state"] == 2


def test_a_command_the_state_accepts_moves_it(capper: Machine):
    assert capper.take("Reset") is True
    assert capper.state == "Resetting"


def test_a_command_the_state_does_not_accept_moves_nothing(capper: Machine):
    assert capper.take("Start") is False
    assert capper.state == "Stopped"


def test_an_acting_state_finishes_on_its_own_only_when_its_time_is_up(capper: Machine):
    capper.take("Reset")

    capper.tick(ACTING / 2)
    assert capper.state == "Resetting"

    capper.tick(ACTING / 2)
    assert capper.state == "Idle"


# --- parameters ----------------------------------------------------------------------------------


def test_a_parameter_within_its_limits_is_taken_and_reported(capper: Machine):
    assert capper.change({"torque_target": 2.2}) == ["torque_target"]
    assert capper.report()["torque_target"] == 2.2


@pytest.mark.parametrize(
    "values",
    [{"torque_target": 50.0}, {"torque_target": -1}, {"torque_target": "tight"}, {"good_count": 7}],
)
def test_a_parameter_outside_the_contract_is_refused(capper: Machine, values: dict):
    assert capper.change(values) == []
    assert capper.status["good_count"] == 0
    assert capper.status["torque_target"] == 2.0


# --- the filler ----------------------------------------------------------------------------------


def test_the_filler_makes_bottles_at_its_speed_and_says_so():
    filler = build("filler")
    bring_to_execute(filler)
    made = filler.status["filled_count"]
    assert isinstance(made, int)

    for _ in range(100):
        filler.tick(0.1)  # 10 seconds at 60 bottles a minute

    assert filler.status["filled_count"] == made + 10
    assert len(filler.outgoing()) == 10


def test_a_filled_bottle_carries_the_level_it_was_filled_to():
    filler = build("filler", fill_target=95.0)
    bring_to_execute(filler)

    filler.tick(1)

    topic, message = filler.outgoing()[0]
    assert topic.endswith("/filler/unit/done")
    assert message == {"unit": "bottle-1", "bottle_fill_level": 95.0, "result": "pass"}


def test_the_filler_makes_nothing_unless_producing():
    filler = build("filler")
    filler.take("Reset")
    filler.tick(ACTING)

    filler.tick(10)

    assert filler.status["filled_count"] == 0


def test_the_filler_uses_up_bottles_and_its_tank():
    filler = build("filler", tank_level=50.0, fill_target=100.0)
    bring_to_execute(filler)
    bottles = filler.status["bottle_supply"]
    assert isinstance(bottles, int)
    filler.tick(10)

    assert filler.status["bottle_supply"] == bottles - 10
    assert filler.status["tank_level"] == pytest.approx(49.9)


@pytest.mark.parametrize("empty", [{"bottle_supply": 2}, {"tank_level": 0.01}])
def test_the_filler_holds_when_a_supply_runs_out(empty: dict):
    filler = build("filler", **empty)
    bring_to_execute(filler)

    for _ in range(50):
        filler.tick(0.1)

    assert filler.state in ("Holding", "Held")


def test_the_filler_goes_on_after_a_refill_and_unhold():
    filler = build("filler", bottle_supply=1)
    bring_to_execute(filler)
    filler.tick(5)
    filler.tick(ACTING)
    assert filler.state == "Held"

    filler.change({"bottle_supply": 100})
    filler.take("Unhold")
    filler.tick(ACTING)
    assert filler.state == "Execute"

    filler.tick(1)
    assert filler.state == "Execute"


def test_a_reset_starts_the_counters_again():
    filler = build("filler")
    bring_to_execute(filler)
    filler.tick(5)
    filler.take("Stop")
    filler.tick(ACTING)
    filler.take("Reset")

    assert filler.status["filled_count"] == 0


# --- the stations --------------------------------------------------------------------------------


def arrive(machine: Machine, level: float = 98.0) -> dict:
    assert machine.unit.unit_topic is not None
    machine.hear(machine.unit.unit_topic, {"unit": "bottle-1", "bottle_fill_level": level})
    return machine.outgoing()[-1][1]


def test_the_capper_closes_a_bottle_with_one_cap_and_counts_it():
    capper = build("capper")
    bring_to_execute(capper)
    caps = capper.status["cap_supply"]
    assert isinstance(caps, int)

    assert arrive(capper)["result"] == "pass"
    assert capper.status["good_count"] == 1
    assert capper.status["cap_supply"] == caps - 1


def test_a_torque_outside_the_limits_makes_a_reject():
    capper = build("capper", torque_target=4.0)
    bring_to_execute(capper)

    assert arrive(capper)["result"] == "reject"
    assert capper.status["reject_count"] == 1
    assert capper.status["good_count"] == 0


def test_the_capper_holds_when_the_caps_run_out():
    capper = build("capper", cap_supply=1)
    bring_to_execute(capper)
    arrive(capper)

    capper.tick(0.1)

    assert capper.state == "Holding"


def test_a_bottle_at_a_station_that_is_not_producing_is_refused_and_not_counted():
    capper = build("capper")

    assert arrive(capper)["result"] == "refused"
    assert capper.status["good_count"] == 0


@pytest.mark.parametrize(
    ("level", "result", "counter"),
    [
        (90.0, "pass", "pass_count"),
        (89.9, "reject", "reject_count"),
    ],
)
def test_the_inspector_judges_by_the_minimum_level(level: float, result: str, counter: str):
    inspector = build("inspector")
    bring_to_execute(inspector)

    assert arrive(inspector, level)["result"] == result
    assert inspector.status[counter] == 1
    assert inspector.status["last_fill_level"] == level


# --- the contract --------------------------------------------------------------------------------


@pytest.mark.parametrize("name", MACHINES)
def test_every_report_keeps_the_contract_in_every_state(name: str):
    machine = build(name)
    schema = status_schema(name)

    for state in machine.unit.states:
        machine.state = state
        report: Any = machine.report()
        assert not list(schema.iter_errors(report)), state


def test_what_a_station_says_about_a_bottle_keeps_the_contract():
    capper = build("capper")
    contract = yaml.safe_load((CONTRACTS / "machines" / "capper.asyncapi.yaml").read_text())
    schema = Draft7Validator(contract["components"]["messages"]["unit_done"]["payload"])
    bring_to_execute(capper)

    message: Any = arrive(capper)

    assert not list(schema.iter_errors(message))
