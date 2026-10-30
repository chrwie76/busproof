"""`expect` waits for the system, and a failure says what it saw.

to_be — a value is reached; rises_by — a counter moves; remains — a value holds, proven by
fresh messages.
"""

import time

import pytest

from busproof import ExpectationFailed, Signal, expect

STATE = "acme/line1/capper/state"
GOOD = "acme/line1/capper/good_count"
REJECTS = "acme/line1/inspector/reject_count"


@pytest.fixture
def state(bus) -> Signal:
    return Signal(bus, STATE, name="capper.state")


@pytest.fixture
def good(bus) -> Signal:
    return Signal(bus, GOOD, name="capper.good_count")


@pytest.fixture
def rejects(bus) -> Signal:
    return Signal(bus, REJECTS, name="inspector.reject_count")


# --- to_be ---------------------------------------------------------------------------------------


async def test_it_passes_at_once_when_the_value_is_already_there(bus, state):
    bus.deliver(STATE, "Execute")

    await expect(state).to_be("Execute", within=0)


async def test_it_waits_for_a_value_that_arrives_later_and_does_not_wait_longer(
    bus, state, deliver_later
):
    bus.deliver(STATE, "Idle")
    deliver_later(0.02, STATE, "Starting")
    deliver_later(0.04, STATE, "Execute")

    started = time.monotonic()
    await expect(state).to_be("Execute", within=5)

    assert time.monotonic() - started < 1, "it should return when Execute arrives, not at 5 s"


async def test_a_failure_lists_each_change_it_saw_with_repeats_collapsed(bus, state, deliver_later):
    bus.deliver(STATE, "Idle")
    deliver_later(0.01, STATE, "Starting")
    deliver_later(0.02, STATE, "Starting")
    deliver_later(0.03, STATE, "Held")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_be("Execute", within=0.1)

    assert str(failure.value) == (
        "expected capper.state to be 'Execute' within 0.1s"
        " — seen: 'Idle' → 'Starting' → 'Held' (3 messages)"
    )


async def test_a_failure_says_when_the_signal_stayed_silent(bus, state):
    bus.deliver(STATE, "Idle")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_be("Execute", within=0.05)

    assert "seen: 'Idle' (no new message in 0.05s)" in str(failure.value)


async def test_a_failure_names_the_topic_when_nothing_ever_arrived(state):
    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_be("Execute", within=0.05)

    assert f"nothing arrived on {STATE}" in str(failure.value)


async def test_a_message_on_another_topic_does_not_count(state, deliver_later):
    deliver_later(0.01, "acme/line1/filler/state", "Execute")

    with pytest.raises(ExpectationFailed):
        await expect(state).to_be("Execute", within=0.05)


async def test_what_the_test_sent_is_not_mistaken_for_the_systems_answer(bus, state):
    await bus.send(STATE, "Execute")

    with pytest.raises(ExpectationFailed):
        await expect(state).to_be("Execute", within=0.05)


def test_a_failed_expectation_is_reported_by_pytest_as_a_failure_not_an_error():
    assert issubclass(ExpectationFailed, AssertionError)


# --- rises_by ------------------------------------------------------------------------------------


async def test_it_passes_when_the_counter_rises_by_the_amount(bus, good, deliver_later):
    bus.deliver(GOOD, 120)
    for step, count in enumerate([121, 123, 125], start=1):
        deliver_later(0.01 * step, GOOD, count)

    await expect(good).rises_by(5, within=5)


async def test_the_baseline_is_the_value_when_the_expectation_starts_not_earlier(
    bus, good, deliver_later
):
    bus.deliver(GOOD, 100)  # during setup
    bus.deliver(GOOD, 110)  # still during setup: this movement is not evidence for the test
    deliver_later(0.01, GOOD, 112)

    with pytest.raises(ExpectationFailed) as failure:
        await expect(good).rises_by(5, within=0.05)

    assert "it rose by 2; seen: 110 → 112 (1 message)" in str(failure.value)


async def test_without_an_earlier_value_the_first_one_in_the_window_is_the_baseline(
    good, deliver_later
):
    deliver_later(0.01, GOOD, 7)
    deliver_later(0.02, GOOD, 12)

    await expect(good).rises_by(5, within=5)


async def test_a_counter_that_rises_too_little_says_by_how_much(bus, good, deliver_later):
    bus.deliver(GOOD, 120)
    deliver_later(0.01, GOOD, 121)
    deliver_later(0.02, GOOD, 122)

    with pytest.raises(ExpectationFailed) as failure:
        await expect(good).rises_by(5, within=0.05)

    assert str(failure.value) == (
        "expected capper.good_count to rise by 5 within 0.05s"
        " — it rose by 2; seen: 120 → 121 → 122 (2 messages)"
    )


async def test_a_value_that_is_not_a_number_is_named(bus, good):
    bus.deliver(GOOD, "many")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(good).rises_by(1, within=0.05)

    assert "'many' is not a number" in str(failure.value)


async def test_a_counter_that_never_reported_names_its_topic(good):
    with pytest.raises(ExpectationFailed) as failure:
        await expect(good).rises_by(1, within=0.05)

    assert f"nothing arrived on {GOOD}" in str(failure.value)


# --- remains -------------------------------------------------------------------------------------


async def test_it_passes_when_fresh_messages_confirm_the_value_for_the_whole_time(
    bus, rejects, deliver_later
):
    bus.deliver(REJECTS, 4)
    deliver_later(0.02, REJECTS, 4)
    deliver_later(0.04, REJECTS, 4)

    started = time.monotonic()
    await expect(rejects).remains(during=0.1)

    assert time.monotonic() - started >= 0.1, "staying is only proven at the end of the time"


async def test_a_change_fails_at_once_and_shows_it(bus, rejects, deliver_later):
    bus.deliver(REJECTS, 4)
    deliver_later(0.01, REJECTS, 4)
    deliver_later(0.02, REJECTS, 5)

    started = time.monotonic()
    with pytest.raises(ExpectationFailed) as failure:
        await expect(rejects).remains(during=5)

    assert time.monotonic() - started < 1, "a change is known at once; no need to wait 5 s"
    assert str(failure.value) == (
        "expected inspector.reject_count to remain 4 for 5s — it changed; seen: 4 → 5 (2 messages)"
    )


async def test_silence_is_not_stability(bus, rejects):
    bus.deliver(REJECTS, 4)  # before the window: says nothing about the window itself

    with pytest.raises(ExpectationFailed) as failure:
        await expect(rejects).remains(during=0.05)

    assert "'unchanged' cannot be told from 'silent'" in str(failure.value)


async def test_a_signal_that_never_reported_cannot_stay(rejects):
    with pytest.raises(ExpectationFailed) as failure:
        await expect(rejects).remains(during=0.05)

    assert f"nothing arrived on {REJECTS}" in str(failure.value)
