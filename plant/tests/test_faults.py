"""Each fault does what FAULTS.md says, and only while it is switched on."""

import json
from pathlib import Path

from plant.contracts import read_unit
from plant.filler import Filler

PLANT = Path(__file__).parents[1]
START = json.loads((PLANT / "config.json").read_text())["units"]["filler"]


def running_filler() -> Filler:
    filler = Filler(read_unit(PLANT.parent / "contracts", "filler"), START, 0.5)
    filler.take("Reset")
    filler.tick(0.5)
    filler.take("Start")
    filler.tick(0.5)
    return filler


def switch(filler: Filler, fault: str | None) -> None:
    filler.hear(filler.fault_topic, {"fault": fault})


def test_a_stuck_counter_stops_in_the_report_while_the_machine_goes_on():
    filler = running_filler()
    filler.tick(2)
    reported = filler.report()["filled_count"]

    switch(filler, "stuck_counter")
    filler.tick(5)

    assert filler.report()["filled_count"] == reported
    assert filler.status["filled_count"] != reported


def test_a_stuck_counter_comes_back_when_the_fault_is_off():
    filler = running_filler()
    switch(filler, "stuck_counter")
    filler.tick(5)

    switch(filler, None)

    assert filler.report()["filled_count"] == filler.status["filled_count"]


def test_skipping_acting_goes_straight_to_the_next_state():
    filler = Filler(read_unit(PLANT.parent / "contracts", "filler"), START, 0.5)
    switch(filler, "skip_acting")

    filler.take("Reset")

    assert filler.state == "Idle"


def test_a_silent_machine_publishes_nothing():
    filler = running_filler()
    switch(filler, "silent")

    assert filler.to_publish(filler.report()) == []


def test_reordered_reports_arrive_the_wrong_way_round():
    filler = running_filler()
    switch(filler, "reorder_reports")
    first: dict[str, object] = {"n": 1}
    second: dict[str, object] = {"n": 2}

    assert filler.to_publish(first) == []
    assert filler.to_publish(dict(first)) == [], "two equal reports swapped would show nothing"
    assert filler.to_publish(second) == [second, first]
