"""Product: a line can show Execute and make nothing — so what it makes is checked on its own."""

import asyncio

from busproof import Signal, expect
from machines import PackagingLine, State


def value_of(signal: Signal) -> int:
    """The last value a signal reported, for a sum over a line that has come to rest."""
    latest = signal.latest()
    assert latest is not None, f"{signal.name} never reported"
    assert isinstance(latest.value, int)
    return latest.value


async def test_a_running_line_makes_good_bottles_and_no_rejects(running_line: PackagingLine):
    await asyncio.gather(
        expect(running_line.filler.filled_count).rises_by(3, within=15),
        expect(running_line.capper.good_count).rises_by(3, within=15),
        expect(running_line.inspector.pass_count).rises_by(3, within=15),
        expect(running_line.capper.reject_count).remains(during=3),
        expect(running_line.inspector.reject_count).remains(during=3),
    )


async def test_an_idle_line_makes_nothing(idle_line: PackagingLine):
    await expect(idle_line.capper.good_count).remains(during=1.5)


async def test_a_low_fill_shows_at_the_end_of_the_line_not_where_it_began(
    running_line: PackagingLine,
):
    await running_line.filler.set(fill_target=80.0)

    await asyncio.gather(
        expect(running_line.inspector.reject_count).rises_by(2, within=20),
        expect(running_line.filler.state).remains(during=8),
        expect(running_line.capper.reject_count).remains(during=8),
    )


async def test_a_bad_torque_is_rejected_at_the_capper_and_never_reaches_the_inspector(
    running_line: PackagingLine,
):
    await running_line.capper.set(torque_target=4.0)

    await expect(running_line.capper.reject_count).rises_by(2, within=15)
    await running_line.stop()
    await expect(running_line.state).to_be(State.STOPPED, within=15)
    # What was already past the capper still arrives; nothing after the torque changed does.
    assert value_of(running_line.inspector.reject_count) == 0


async def test_every_bottle_is_accounted_for_when_the_line_has_run_empty(
    running_line: PackagingLine,
):
    await expect(running_line.inspector.pass_count).rises_by(3, within=15)

    await running_line.stop()
    await expect(running_line.state).to_be(State.STOPPED, within=15)
    await expect(running_line.scu.state).to_be(State.STOPPED, within=15)

    filled = value_of(running_line.filler.filled_count)
    accounted = (
        value_of(running_line.capper.reject_count)
        + value_of(running_line.inspector.pass_count)
        + value_of(running_line.inspector.reject_count)
        + value_of(running_line.scu.in_transit)
        + value_of(running_line.scu.lost)
    )
    assert filled == accounted
    assert value_of(running_line.scu.in_transit) == 0
    assert value_of(running_line.scu.lost) == 0


async def test_an_abort_loses_what_is_on_the_belt_and_says_how_many(running_line: PackagingLine):
    await expect(running_line.filler.filled_count).rises_by(2, within=15)

    await running_line.abort()

    await expect(running_line.scu.lost).rises_by(1, within=5)
