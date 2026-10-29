"""`expect(...).to_equal(...)` waits for the system, and a failure says what it saw."""

import time

import pytest

from busproof import ExpectationFailed, Signal, expect

STATE = "acme/line1/capper/state"


@pytest.fixture
def state(bus) -> Signal:
    return Signal(bus, STATE, name="capper.state")


async def test_it_passes_at_once_when_the_value_is_already_there(bus, state):
    bus.deliver(STATE, "Execute")

    await expect(state).to_equal("Execute", within_s=0)


async def test_it_waits_for_a_value_that_arrives_later_and_does_not_wait_longer(
    bus, state, deliver_later
):
    bus.deliver(STATE, "Idle")
    deliver_later(0.02, STATE, "Starting")
    deliver_later(0.04, STATE, "Execute")

    started = time.monotonic()
    await expect(state).to_equal("Execute", within_s=5)

    assert time.monotonic() - started < 1, "it should return when Execute arrives, not at 5 s"


async def test_a_failure_lists_each_change_it_saw_with_repeats_collapsed(bus, state, deliver_later):
    bus.deliver(STATE, "Idle")
    deliver_later(0.01, STATE, "Starting")
    deliver_later(0.02, STATE, "Starting")
    deliver_later(0.03, STATE, "Held")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_equal("Execute", within_s=0.1)

    assert str(failure.value) == (
        "expected capper.state to equal 'Execute' within 0.1s"
        " — seen: 'Idle' → 'Starting' → 'Held' (3 messages)"
    )


async def test_a_failure_says_when_the_signal_stayed_silent(bus, state):
    bus.deliver(STATE, "Idle")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_equal("Execute", within_s=0.05)

    assert "seen: 'Idle' (no new message in 0.05s)" in str(failure.value)


async def test_a_failure_names_the_topic_when_nothing_ever_arrived(state):
    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_equal("Execute", within_s=0.05)

    assert f"nothing arrived on {STATE}" in str(failure.value)


async def test_a_message_on_another_topic_does_not_count(state, deliver_later):
    deliver_later(0.01, "acme/line1/filler/state", "Execute")

    with pytest.raises(ExpectationFailed):
        await expect(state).to_equal("Execute", within_s=0.05)


async def test_what_the_test_sent_is_not_mistaken_for_the_systems_answer(bus, state):
    await bus.send(STATE, "Execute")

    with pytest.raises(ExpectationFailed):
        await expect(state).to_equal("Execute", within_s=0.05)


def test_a_failed_expectation_is_reported_by_pytest_as_a_failure_not_an_error():
    assert issubclass(ExpectationFailed, AssertionError)
