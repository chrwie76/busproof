"""Timing: a machine keeps reporting when nothing happens — otherwise silence hides a dead one."""

from busproof import expect
from machines import PackagingLine, State


async def test_an_idle_machine_keeps_confirming_its_state(idle_line: PackagingLine):
    await expect(idle_line.capper.state).to_be(State.IDLE, within=5)

    await expect(idle_line.capper.state).remains(during=0.1)
