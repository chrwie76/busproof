"""Timing: a bottle takes as long as line.yaml says, and the belt stands still in a hold."""

from busproof import Bus, LineContract, Message, expect
from machines import PackagingLine, State

TRANSPORT_SECONDS = 3 + 2  # filler -> capper -> inspector, as in line.yaml
# The steps of the plant and the way over the broker: never faster, a little later.
TOLERANCE_SECONDS = 1.0


def verdicts(bus: Bus, contract: LineContract, machine: str) -> list[Message]:
    """What `machine` said about bottles, in the order it arrived."""
    topic = contract.topics(machine, "unit").topic
    return [message for message in bus.recorder.messages() if message.topic == topic]


async def test_a_bottle_takes_as_long_as_the_line_says(
    running_line: PackagingLine, bus: Bus, contract: LineContract
):
    await expect(running_line.inspector.pass_count).rises_by(1, within=15)

    left = verdicts(bus, contract, "filler")[0]
    assert isinstance(left.value, dict)
    judged = next(
        message
        for message in verdicts(bus, contract, "inspector")
        if isinstance(message.value, dict) and message.value["unit"] == left.value["unit"]
    )
    assert TRANSPORT_SECONDS <= judged.at - left.at <= TRANSPORT_SECONDS + TOLERANCE_SECONDS


async def test_nothing_moves_while_the_line_holds_and_it_goes_on_after(
    running_line: PackagingLine,
):
    await expect(running_line.inspector.pass_count).rises_by(1, within=15)

    await running_line.hold()
    await expect(running_line.scu.state).to_be(State.HELD, within=10)
    await expect(running_line.inspector.pass_count).remains(during=2)

    await running_line.unhold()
    await expect(running_line.inspector.pass_count).rises_by(2, within=15)
