"""Control: a command moves the line through its states; one it does not accept moves nothing."""

from busproof import expect
from machines import PackagingLine, State


async def test_reset_brings_the_line_from_stopped_to_idle(line: PackagingLine):
    await line.reset()

    await expect(line.state).to_be(State.IDLE, within=10)


async def test_start_brings_an_idle_line_to_execute(idle_line: PackagingLine):
    await idle_line.start()

    await expect(idle_line.state).to_be(State.EXECUTE, within=10)


async def test_hold_brings_a_running_line_to_held(running_line: PackagingLine):
    await running_line.hold()

    await expect(running_line.state).to_be(State.HELD, within=10)


async def test_stop_brings_a_running_line_to_stopped(running_line: PackagingLine):
    await running_line.stop()

    await expect(running_line.state).to_be(State.STOPPED, within=10)


async def test_abort_stops_every_machine_from_the_scu(running_line: PackagingLine):
    await running_line.abort()

    await expect(running_line.state).to_be(State.ABORTED, within=10)
    await expect(running_line.scu.state).to_be(State.ABORTED, within=10)


async def test_a_command_the_state_does_not_accept_moves_nothing(line: PackagingLine):
    await line.start()  # Start is accepted in Idle, not in Stopped

    await expect(line.state).remains(during=1.5)
    await expect(line.scu.state).remains(during=1.5)
