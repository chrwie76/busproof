"""Product: a line can show Execute and make nothing — so what it makes is checked on its own."""

import asyncio

from busproof import expect
from machines import PackagingLine


async def test_a_running_line_makes_good_units_and_no_rejects(running_line: PackagingLine):
    await asyncio.gather(
        expect(running_line.filler.filled_count).rises_by(5, within=5),
        expect(running_line.capper.good_count).rises_by(5, within=5),
        expect(running_line.inspector.pass_count).rises_by(5, within=5),
        expect(running_line.inspector.reject_count).remains(during=0.1),
    )


async def test_an_idle_line_makes_nothing(idle_line: PackagingLine):
    await expect(idle_line.capper.good_count).remains(during=0.1)
