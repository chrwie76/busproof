"""Catch power: with a fault switched on in the plant, do the checks really find it?

A test that was never seen to fail proves little. Here each fault of demo/plant/FAULTS.md is
switched on, and the check that should find it has to find it.
"""

from pathlib import Path

import pytest

from busproof import Bus, ExpectationFailed, LineContract, expect
from checks import (
    accounted_for,
    first_report_of,
    illegal_changes,
    switch_fault,
    value_of,
    went_down,
)
from machines import PackagingLine, State


async def test_a_stuck_counter_is_found_by_expecting_movement(running_line: PackagingLine):
    await switch_fault(running_line.filler, "stuck_counter")

    with pytest.raises(ExpectationFailed, match="it rose by 0"):
        await expect(running_line.filler.filled_count).rises_by(3, within=6)


async def test_skipped_states_are_found_against_the_state_machine(
    line: PackagingLine, state_machine: Path
):
    await switch_fault(line.capper, "skip_acting")

    await line.reset()
    await expect(line.scu.state).to_be(State.IDLE, within=10)

    assert illegal_changes(line.capper.state, state_machine)


async def test_a_clean_run_shows_no_illegal_state_change(
    idle_line: PackagingLine, state_machine: Path
):
    line = idle_line
    await line.start()
    await expect(line.state).to_be(State.EXECUTE, within=10)
    await line.stop()
    await expect(line.state).to_be(State.STOPPED, within=15)

    for machine in (line.filler, line.capper, line.inspector):
        assert not illegal_changes(machine.state, state_machine), machine.name


async def test_a_silent_machine_is_found_by_the_scu_though_its_last_will_never_fires(
    running_line: PackagingLine,
):
    await switch_fault(running_line.capper, "silent")

    await expect(running_line.scu.faulted_machine).to_be("capper", within=10)
    await expect(running_line.scu.state).to_be(State.HELD, within=10)
    await expect(running_line.capper.online).to_be(True, within=1)


async def test_reordered_reports_are_found_by_a_counter_going_down(
    running_line: PackagingLine, bus: Bus
):
    since = len(bus.recorder)
    await switch_fault(running_line.filler, "reorder_reports")

    await expect(running_line.filler.filled_count).rises_by(4, within=15)

    assert went_down(running_line.filler.filled_count, since)


async def test_a_clean_run_has_no_counter_going_down(running_line: PackagingLine, bus: Bus):
    since = len(bus.recorder)

    await expect(running_line.filler.filled_count).rises_by(4, within=15)

    assert not went_down(running_line.filler.filled_count, since)


async def test_a_false_claim_is_found_by_comparing_with_the_machines(
    idle_line: PackagingLine, bus: Bus, contract: LineContract
):
    await switch_fault(idle_line.scu, "false_claim")

    await idle_line.start()
    await expect(idle_line.scu.state).to_be(State.EXECUTE, within=10)
    await expect(idle_line.state).to_be(State.EXECUTE, within=10)

    claim = first_report_of(bus, contract, "scu", State.EXECUTE)
    assert any(
        first_report_of(bus, contract, machine, State.EXECUTE) > claim
        for machine in contract.machines
    )


async def test_vanished_bottles_are_found_by_the_balance(running_line: PackagingLine):
    await switch_fault(running_line.scu, "lose_bottles")
    await expect(running_line.filler.filled_count).rises_by(6, within=15)

    await running_line.stop()
    await expect(running_line.state).to_be(State.STOPPED, within=15)
    await expect(running_line.scu.state).to_be(State.STOPPED, within=15)

    assert value_of(running_line.filler.filled_count) > accounted_for(running_line)
