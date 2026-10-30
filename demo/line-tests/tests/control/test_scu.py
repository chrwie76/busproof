"""Control: what the SCU should do, as line.yaml says it, and what it claims against the truth."""

import asyncio

from busproof import Bus, LineContract, expect
from checks import first_report_of
from machines import PackagingLine, State


def command_order(bus: Bus, contract: LineContract, command: str) -> list[str]:
    """The machines, in the order the SCU's `command` reached them on the bus."""
    topics = {contract.topics(name, command).topic: name for name in contract.machines}
    return [
        topics[message.topic]
        for message in bus.recorder.messages()
        if message.direction == "received"
        and message.topic in topics
        and message.value == {"command": command}
    ]


async def test_the_line_starts_from_its_end(
    idle_line: PackagingLine, bus: Bus, contract: LineContract
):
    await idle_line.start()
    await expect(idle_line.state).to_be(State.EXECUTE, within=10)

    assert command_order(bus, contract, "Start") == ["inspector", "capper", "filler"]


async def test_the_line_stops_from_its_beginning(
    running_line: PackagingLine, bus: Bus, contract: LineContract
):
    await running_line.stop()
    await expect(running_line.state).to_be(State.STOPPED, within=15)

    assert command_order(bus, contract, "Stop") == ["filler", "capper", "inspector"]


async def test_the_scu_claims_execute_only_after_every_machine_reported_it(
    idle_line: PackagingLine, bus: Bus, contract: LineContract
):
    await idle_line.start()
    await asyncio.gather(
        expect(idle_line.state).to_be(State.EXECUTE, within=10),
        expect(idle_line.scu.state).to_be(State.EXECUTE, within=10),
    )

    claim = first_report_of(bus, contract, "scu", State.EXECUTE)
    for machine in contract.machines:
        assert first_report_of(bus, contract, machine, State.EXECUTE) < claim, machine


async def test_a_machine_stopped_behind_the_scus_back_makes_the_line_hold(
    running_line: PackagingLine,
):
    await running_line.capper.send("Stop")  # as the web page can

    await expect(running_line.scu.faulted_machine).to_be("capper", within=10)
    await expect(running_line.scu.state).to_be(State.HELD, within=10)
    await expect(running_line.filler.state).to_be(State.HELD, within=10)
    await expect(running_line.inspector.state).to_be(State.HELD, within=10)
    await expect(running_line.capper.state).to_be(State.STOPPED, within=10)


async def test_a_machine_out_of_caps_holds_the_line_until_it_is_refilled(
    running_line: PackagingLine,
):
    await running_line.capper.set(cap_supply=2)

    await expect(running_line.scu.faulted_machine).to_be("capper", within=20)
    await expect(running_line.scu.state).to_be(State.HELD, within=10)
    await expect(running_line.state).to_be(State.HELD, within=10)

    await running_line.capper.set(cap_supply=1000)
    await running_line.unhold()

    await expect(running_line.state).to_be(State.EXECUTE, within=10)
    await expect(running_line.scu.faulted_machine).to_be(None, within=10)
