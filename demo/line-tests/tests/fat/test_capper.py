"""Factory acceptance: the capper alone, with no line and no SCU — as at its maker's.

Run with `make fat`: only the broker and this one machine are started.
"""

from busproof import Bus, expect
from machines import Capper, State


async def test_reset_brings_it_to_idle(stopped_capper: Capper):
    await stopped_capper.send("Reset")

    await expect(stopped_capper.state).to_be(State.IDLE, within=5)


async def test_start_brings_it_to_execute_and_it_counts(stopped_capper: Capper):
    await stopped_capper.send("Reset")
    await expect(stopped_capper.state).to_be(State.IDLE, within=5)

    await stopped_capper.send("Start")

    await expect(stopped_capper.state).to_be(State.EXECUTE, within=5)
    await expect(stopped_capper.good_count).rises_by(2, within=5)


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
