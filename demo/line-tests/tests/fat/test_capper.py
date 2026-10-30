"""Factory acceptance: the capper alone, with no line and no SCU — as at its maker's.

Run with `make fat`: only the broker and this one machine are started.
"""

from busproof import Bus, expect
from machines import Capper, State


async def test_reset_brings_it_to_idle(stopped_capper: Capper):
    await stopped_capper.send("Reset")

    await expect(stopped_capper.state).to_be(State.IDLE, within=5)


async def running(capper: Capper) -> None:
    await capper.send("Reset")
    await expect(capper.state).to_be(State.IDLE, within=5)
    await capper.send("Start")
    await expect(capper.state).to_be(State.EXECUTE, within=5)


async def test_a_bottle_that_arrives_is_closed_and_counted(stopped_capper: Capper):
    await running(stopped_capper)

    await stopped_capper.set(unit="bottle-1", bottle_fill_level=98.0)

    await expect(stopped_capper.good_count).rises_by(1, within=5)
    await expect(stopped_capper.result).to_be("pass", within=5)


async def test_a_bad_torque_makes_a_reject(stopped_capper: Capper):
    await stopped_capper.set(torque_target=4.0)
    await running(stopped_capper)

    await stopped_capper.set(unit="bottle-1", bottle_fill_level=98.0)

    await expect(stopped_capper.reject_count).rises_by(1, within=5)
    await expect(stopped_capper.result).to_be("reject", within=5)


async def test_a_bottle_it_cannot_work_on_is_refused(stopped_capper: Capper):
    await stopped_capper.set(unit="bottle-1", bottle_fill_level=98.0)

    await expect(stopped_capper.result).to_be("refused", within=5)
    await expect(stopped_capper.good_count).to_be(0, within=5)


async def test_it_holds_when_the_caps_run_out(stopped_capper: Capper):
    await stopped_capper.set(cap_supply=1)
    await running(stopped_capper)

    await stopped_capper.set(unit="bottle-1", bottle_fill_level=98.0)

    await expect(stopped_capper.state).to_be(State.HELD, within=5)


async def test_a_command_its_state_does_not_accept_moves_nothing(stopped_capper: Capper):
    await stopped_capper.send("Start")

    await expect(stopped_capper.state).remains(during=1.5)


async def test_it_keeps_reporting_when_nothing_happens(stopped_capper: Capper):
    await expect(stopped_capper.state).remains(during=1.5)


async def test_what_the_test_sends_is_not_heard_back_as_the_machines_answer(
    stopped_capper: Capper, bus: Bus
):
    await stopped_capper.send("Reset")
    await expect(stopped_capper.state).to_be(State.IDLE, within=5)

    sent_topics = {
        message.topic for message in bus.recorder.messages() if message.direction == "sent"
    }
    received = [
        message
        for message in bus.recorder.messages()
        if message.direction == "received" and message.topic in sent_topics
    ]
    assert sent_topics
    assert not received
