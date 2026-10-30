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
    start = {"in_transit": 0, "lost": 0, "faulted_machine": None}
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
    assert commands_sent(scu) == ["filler"], "the rest go on until the belt has run empty"

    report(scu, "filler", "Stopped")
    scu.tick(0.1)
    assert commands_sent(scu) == ["capper", "inspector"]


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


def test_a_new_order_clears_the_memory_of_a_fault(scu: Scu):
    bring_to_execute(scu)
    report(scu, "capper", "Stopped")
    scu.tick(0.1)
    assert scu.status["faulted_machine"] == "capper"

    scu.take("Stop")

    assert scu.status["faulted_machine"] is None


def test_a_machine_that_holds_on_its_own_holds_the_line_and_unhold_brings_it_back(scu: Scu):
    bring_to_execute(scu)
    report(scu, "capper", "Held")  # its caps ran out
    scu.tick(0.1)
    report(scu, "filler", "Held")
    report(scu, "inspector", "Held")
    scu.tick(0.1)
    assert scu.state == "Held"
    assert scu.status["faulted_machine"] == "capper"
    scu.outgoing()

    scu.take("Unhold")
    assert sorted(commands_sent(scu)) == ["capper", "filler", "inspector"]
    assert scu.status["faulted_machine"] is None

    report_all(scu, "Execute")
    scu.tick(0.1)
    assert scu.state == "Execute"


# --- the transport -------------------------------------------------------------------------------


def filled(scu: Scu, unit: str = "bottle-1", level: float = 98.0) -> None:
    topic = scu.plan.machines["filler"].unit_done_topic
    assert topic is not None
    scu.hear(topic, {"unit": unit, "bottle_fill_level": level, "result": "pass"})


def answer(scu: Scu, station: str, result: str, unit: str = "bottle-1") -> None:
    topic = scu.plan.machines[station].unit_done_topic
    assert topic is not None
    scu.hear(topic, {"unit": unit, "bottle_fill_level": 98.0, "result": result})


def arrivals(scu: Scu) -> list[tuple[str, dict]]:
    return [(topic.split("/")[-2], message) for topic, message in scu.outgoing()]


def keep_alive(scu: Scu) -> None:
    report_all(scu, "Execute")


def advance(scu: Scu, seconds: float) -> None:
    """Time passes as it does on the line: in small steps, with the machines reporting."""
    for _ in range(round(seconds * 10)):
        for machine, state in scu.machine_states.items():
            report(scu, machine, state)
        scu.tick(0.1)


def test_a_bottle_travels_as_long_as_the_line_says(scu: Scu):
    bring_to_execute(scu)
    filled(scu)

    advance(scu, 2.8)
    assert arrivals(scu) == []
    assert scu.status["in_transit"] == 1

    advance(scu, 0.3)
    assert arrivals(scu) == [("capper", {"unit": "bottle-1", "bottle_fill_level": 98.0})]


def test_a_passed_bottle_goes_on_to_the_next_station(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    advance(scu, 3.1)
    scu.outgoing()
    keep_alive(scu)

    answer(scu, "capper", "pass")
    advance(scu, 2.1)

    assert arrivals(scu)[0][0] == "inspector"


def test_a_rejected_bottle_leaves_the_line(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    advance(scu, 3.1)
    scu.outgoing()
    keep_alive(scu)

    answer(scu, "capper", "reject")
    advance(scu, 5)

    assert arrivals(scu) == []
    assert scu.status["in_transit"] == 0
    assert scu.status["lost"] == 0


def test_a_bottle_is_finished_after_the_last_station(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    advance(scu, 3.1)
    keep_alive(scu)
    answer(scu, "capper", "pass")
    advance(scu, 2.1)
    keep_alive(scu)
    answer(scu, "inspector", "pass")
    scu.tick(0.1)

    assert scu.status["in_transit"] == 0
    assert scu.status["lost"] == 0


def test_the_belt_stands_still_while_the_line_holds(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.take("Hold")
    report_all(scu, "Held")
    scu.outgoing()
    advance(scu, 10)

    assert arrivals(scu) == []
    assert scu.status["in_transit"] == 1
    assert scu.status["lost"] == 0


def test_stopping_lets_the_belt_run_empty_before_the_rest_stop(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.take("Stop")
    report(scu, "filler", "Stopped")
    scu.outgoing()

    advance(scu, 3.1)
    assert arrivals(scu)[0][0] == "capper"

    answer(scu, "capper", "pass")
    advance(scu, 2.1)
    assert [name for name, _ in arrivals(scu)] == ["inspector"]

    answer(scu, "inspector", "pass")
    scu.tick(0.1)
    assert commands_sent(scu) == ["capper", "inspector"]
    assert scu.status["lost"] == 0


def test_an_abort_loses_what_is_on_the_belt_and_says_so(scu: Scu):
    bring_to_execute(scu)
    filled(scu, "bottle-1")
    filled(scu, "bottle-2")

    scu.take("Abort")
    scu.tick(0.1)

    assert scu.status["lost"] == 2
    assert scu.status["in_transit"] == 0


def test_a_stop_from_a_standing_belt_loses_what_is_on_it(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.take("Hold")
    report_all(scu, "Held")
    scu.tick(0.1)

    scu.take("Stop")
    scu.tick(0.1)

    assert scu.status["lost"] == 1


def test_a_bottle_a_station_refuses_is_lost(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    advance(scu, 3.1)
    keep_alive(scu)

    answer(scu, "capper", "refused")
    scu.tick(0.1)

    assert scu.status["lost"] == 1


def test_a_bottle_for_a_station_that_is_gone_is_lost(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.hear(scu.plan.machines["capper"].online_topic, {"online": False})

    scu.take("Stop")
    report(scu, "filler", "Stopped")
    advance(scu, 3.1)

    assert scu.status["lost"] == 1
    assert scu.status["in_transit"] == 0


def test_a_station_going_silent_does_not_keep_the_line_waiting_for_its_answer(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.take("Stop")
    report(scu, "filler", "Stopped")
    advance(scu, 3.1)
    scu.outgoing()

    scu.tick(3.1)

    assert scu.status["in_transit"] == 0
    assert scu.status["lost"] == 1


def test_an_answer_that_comes_after_it_was_given_up_counts_nothing(scu: Scu):
    bring_to_execute(scu)
    filled(scu)
    scu.take("Abort")
    scu.tick(0.1)

    answer(scu, "capper", "pass")
    advance(scu, 5)

    assert scu.status["in_transit"] == 0
    assert scu.status["lost"] == 1


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
