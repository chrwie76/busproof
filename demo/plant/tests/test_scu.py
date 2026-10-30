"""The SCU passes commands on in order, waits for the machines, and notices what they report."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft7Validator

from plant.contracts import read_plan, read_unit
from plant.scu import Scu

CONTRACTS = Path(__file__).parents[2] / "contracts"
MACHINES = ["filler", "capper", "inspector"]
NUMBERS = {"Stopped": 2, "Idle": 4, "Starting": 3, "Execute": 6, "Stopping": 7, "Held": 11}


@pytest.fixture
def scu() -> Scu:
    start = {"in_transit": 0, "faulted_machine": None}
    return Scu(read_unit(CONTRACTS, "scu"), read_plan(CONTRACTS), start, 0.5, 3.0)


def report(scu: Scu, machine: str, state: str) -> None:
    scu.hear(scu.plan.machines[machine].status_topic, {"state": NUMBERS[state]})


def report_all(scu: Scu, state: str) -> None:
    for machine in MACHINES:
        report(scu, machine, state)


def bring_to_execute(scu: Scu) -> None:
    report_all(scu, "Stopped")
    scu.take("Reset")
    report_all(scu, "Idle")
    scu.tick(0.1)
    scu.take("Start")
    report_all(scu, "Execute")
    scu.tick(0.1)
    scu.outgoing()
    assert scu.state == "Execute"


def commands_sent(scu: Scu) -> list[str]:
    return [topic.split("/")[-2] for topic, _ in scu.outgoing()]


def test_it_starts_the_line_from_its_end(scu: Scu):
    report_all(scu, "Stopped")
    scu.take("Reset")
    report_all(scu, "Idle")
    scu.tick(0.1)
    scu.outgoing()

    scu.take("Start")

    assert commands_sent(scu) == ["inspector", "capper", "filler"]


def test_it_stops_the_line_from_its_beginning(scu: Scu):
    bring_to_execute(scu)

    scu.take("Stop")

    assert commands_sent(scu) == ["filler", "capper", "inspector"]


def test_a_command_it_refuses_is_not_passed_on(scu: Scu):
    assert scu.take("Start") is False
    assert scu.outgoing() == []


def test_its_acting_state_ends_only_when_every_machine_has_got_there(scu: Scu):
    report_all(scu, "Stopped")
    scu.take("Reset")
    report(scu, "filler", "Idle")
    report(scu, "capper", "Idle")

    scu.tick(10)
    assert scu.state == "Resetting"

    report(scu, "inspector", "Idle")
    scu.tick(0.1)
    assert scu.state == "Idle"


def test_a_machine_stopped_behind_its_back_makes_the_line_hold(scu: Scu):
    bring_to_execute(scu)

    report(scu, "capper", "Stopped")
    scu.tick(0.1)

    assert scu.state == "Holding"
    assert scu.status["faulted_machine"] == "capper"
    assert commands_sent(scu) == ["filler", "capper", "inspector"]


def test_it_holds_without_waiting_for_the_machine_that_failed(scu: Scu):
    bring_to_execute(scu)
    report(scu, "capper", "Stopped")
    scu.tick(0.1)

    report(scu, "filler", "Held")
    report(scu, "inspector", "Held")
    scu.tick(0.1)

    assert scu.state == "Held"


def test_a_machine_that_is_gone_makes_the_line_hold(scu: Scu):
    bring_to_execute(scu)

    scu.hear(scu.plan.machines["inspector"].online_topic, {"online": False})
    scu.tick(0.1)

    assert scu.state == "Holding"
    assert scu.status["faulted_machine"] == "inspector"


def test_a_machine_gone_silent_makes_the_line_hold(scu: Scu):
    bring_to_execute(scu)
    scu.tick(2)
    report(scu, "filler", "Execute")
    report(scu, "inspector", "Execute")

    scu.tick(1.1)

    assert scu.state == "Holding"
    assert scu.status["faulted_machine"] == "capper"


def test_with_no_machine_left_it_claims_nothing(scu: Scu):
    report_all(scu, "Stopped")
    scu.take("Reset")
    for machine in MACHINES:
        scu.hear(scu.plan.machines[machine].online_topic, {"online": False})

    scu.tick(0.1)

    assert scu.state == "Resetting"


def test_a_reset_clears_the_memory_of_a_fault(scu: Scu):
    bring_to_execute(scu)
    report(scu, "capper", "Stopped")
    scu.tick(0.1)
    scu.take("Stop")
    report(scu, "filler", "Stopped")
    report(scu, "inspector", "Stopped")
    scu.tick(0.1)
    assert scu.state == "Stopped"

    scu.take("Reset")

    assert scu.status["faulted_machine"] is None


def test_every_report_keeps_the_contract(scu: Scu):
    contract = yaml.safe_load((CONTRACTS / "scu.asyncapi.yaml").read_text())
    schema = Draft7Validator(contract["components"]["messages"]["status"]["payload"])

    for name in scu.unit.states:
        scu.state = name
        value: Any = scu.report()
        assert not list(schema.iter_errors(value)), name


def test_a_state_number_no_state_has_is_refused(scu: Scu):
    with pytest.raises(ValueError, match="no state has the number 99"):
        scu.hear(scu.plan.machines["capper"].status_topic, {"state": 99})
