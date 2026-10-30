"""Product: a line can show Execute and make nothing — so what it makes is checked on its own."""

import asyncio

import pytest

from busproof import expect
from machines import PackagingLine


async def test_a_running_line_fills_and_caps(running_line: PackagingLine):
    await asyncio.gather(
        expect(running_line.filler.filled_count).rises_by(3, within=15),
        expect(running_line.capper.good_count).rises_by(3, within=15),
        expect(running_line.capper.reject_count).remains(during=3),
    )


@pytest.mark.needs_transport
async def test_good_bottles_reach_the_end_of_the_line(running_line: PackagingLine):
    await asyncio.gather(
        expect(running_line.inspector.pass_count).rises_by(3, within=15),
        expect(running_line.inspector.reject_count).remains(during=3),
    )


async def test_an_idle_line_makes_nothing(idle_line: PackagingLine):
    await expect(idle_line.capper.good_count).remains(during=1.5)
