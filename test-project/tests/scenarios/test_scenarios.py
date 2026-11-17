"""Scenarios: the plant starts from other settings, and the line does what they lead to."""

import asyncio

import pytest

from busproof import expect
from machines import PackagingLine, State


@pytest.mark.scenario("low_caps")
async def test_with_few_caps_the_line_holds_by_itself_and_a_refill_brings_it_back(
    running_line: PackagingLine,
):
    await expect(running_line.scu.faulted_machine).to_be("capper", within=20)
    await expect(running_line.scu.state).to_be(State.HELD, within=10)

    await running_line.capper.set(cap_supply=100)
    await running_line.unhold()

    await expect(running_line.state).to_be(State.EXECUTE, within=10)
    await expect(running_line.capper.good_count).rises_by(1, within=10)


@pytest.mark.scenario("under_filled")
async def test_a_filler_set_too_low_makes_rejects_from_the_first_bottle(
    running_line: PackagingLine,
):
    await asyncio.gather(
        expect(running_line.inspector.reject_count).rises_by(3, within=20),
        expect(running_line.inspector.pass_count).remains(during=8),
    )


@pytest.mark.scenario("fast")
async def test_at_twice_the_speed_the_filler_makes_bottles_twice_as_fast(
    running_line: PackagingLine,
):
    await expect(running_line.filler.filled_count).rises_by(6, within=5)


async def test_without_a_scenario_the_plant_is_as_configured_again(running_line: PackagingLine):
    await expect(running_line.inspector.pass_count).rises_by(2, within=15)
