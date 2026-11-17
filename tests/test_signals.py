"""A signal picks its value out of a payload and says what a number means; a consensus has a
value only when all members agree — one member never speaks for all."""

from enum import IntEnum

import pytest

from busproof import Consensus, ExpectationFailed, Mixed, Signal, expect

MACHINE = "acme/plant1/packaging/line1/capper"
FILLER = "acme/line1/filler/state"
CAPPER = "acme/line1/capper/state"


class State(IntEnum):
    """Some PackTags state numbers, as a test project would write them."""

    STOPPED = 2
    STARTING = 3
    IDLE = 4
    EXECUTE = 6


@pytest.fixture
def rejects(bus) -> Signal:
    return Signal(bus, MACHINE, "capper.reject_count", path=("reject_count",))


@pytest.fixture
def state(bus) -> Signal:
    return Signal(bus, MACHINE, "capper.state", path=("state",), enum=State)


# --- a value in a payload ------------------------------------------------------------------------


def test_a_signal_picks_its_field_out_of_the_machines_message(bus, rejects):
    bus.deliver(MACHINE, {"state": "Execute", "good_count": 120, "reject_count": 4})

    latest = rejects.latest()
    assert latest is not None and latest.value == 4


def test_a_message_without_the_field_does_not_count(bus, rejects):
    bus.deliver(MACHINE, {"reject_count": 4})
    bus.deliver(MACHINE, {"state": "Held"})
    bus.deliver(MACHINE, "not a payload with fields")

    assert [message.value for message in rejects.fresh(since=0)] == [4]


def test_a_path_reaches_into_nested_payloads(bus):
    temperature = Signal(bus, MACHINE, "capper.temperature", path=("motor", "temperature"))
    bus.deliver(MACHINE, {"motor": {"temperature": 41.5}})

    latest = temperature.latest()
    assert latest is not None and latest.value == 41.5


async def test_a_machine_repeating_its_whole_state_confirms_that_a_value_remains(
    bus, rejects, deliver_later
):
    bus.deliver(MACHINE, {"good_count": 120, "reject_count": 4})
    deliver_later(0.02, MACHINE, {"good_count": 121, "reject_count": 4})

    await expect(rejects).remains(during=0.05)


async def test_a_failure_names_the_field_and_the_topic_when_nothing_arrived(bus, rejects):
    bus.deliver(MACHINE, {"state": "Idle"})

    with pytest.raises(ExpectationFailed) as failure:
        await expect(rejects).to_be(0, within=0.05)

    assert f"nothing arrived on {MACHINE} (payload field reject_count)" in str(failure.value)


# --- what a number means -------------------------------------------------------------------------


def test_a_number_on_the_wire_is_read_as_its_name(bus, state):
    bus.deliver(MACHINE, {"state": 6})

    latest = state.latest()
    assert latest is not None and latest.value is State.EXECUTE


def test_the_recorder_keeps_the_number_that_was_on_the_wire(bus, state):
    bus.deliver(MACHINE, {"state": 6})

    assert bus.recorder.messages()[0].value == {"state": 6}


async def test_a_failure_shows_the_name_and_the_number(bus, state, deliver_later):
    bus.deliver(MACHINE, {"state": 4})
    deliver_later(0.01, MACHINE, {"state": 3})

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_be(State.EXECUTE, within=0.05)

    assert str(failure.value) == (
        "expected capper.state to be EXECUTE (6) within 0.05s"
        " — seen: IDLE (4) → STARTING (3) (1 message)"
    )


async def test_a_number_the_enum_does_not_know_stays_a_number_and_shows(bus, state):
    bus.deliver(MACHINE, {"state": 99})

    with pytest.raises(ExpectationFailed) as failure:
        await expect(state).to_be(State.EXECUTE, within=0.05)

    assert "seen: 99 (no new message" in str(failure.value)


# --- consensus -----------------------------------------------------------------------------------


@pytest.fixture
def line_state(bus) -> Consensus:
    members = [Signal(bus, FILLER, "filler.state"), Signal(bus, CAPPER, "capper.state")]
    return Consensus(bus, members, name="line.state")


def test_it_has_no_value_until_every_member_has_reported(bus, line_state):
    bus.deliver(FILLER, "Execute")

    assert line_state.latest() is None


def test_members_that_agree_give_their_value(bus, line_state):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Execute")

    latest = line_state.latest()
    assert latest is not None and latest.value == "Execute"


def test_members_that_disagree_give_mixed_and_name_each_one(bus, line_state):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Idle")

    latest = line_state.latest()
    assert latest is not None and latest.value == Mixed(
        (("filler.state", "Execute"), ("capper.state", "Idle"))
    )
    assert repr(latest.value) == "mixed(filler.state='Execute', capper.state='Idle')"


def test_a_member_that_agrees_on_none_still_agrees(bus, line_state):
    bus.deliver(FILLER, None)
    bus.deliver(CAPPER, None)

    latest = line_state.latest()
    assert latest is not None and latest.value is None


async def test_the_line_is_in_execute_only_when_the_last_machine_gets_there(
    bus, line_state, deliver_later
):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Idle")
    deliver_later(0.02, CAPPER, "Starting")
    deliver_later(0.04, CAPPER, "Execute")

    await expect(line_state).to_be("Execute", within=5)


async def test_a_half_running_line_fails_and_shows_who_disagrees(bus, line_state):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Idle")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(line_state).to_be("Execute", within=0.05)

    assert str(failure.value) == (
        "expected line.state to be 'Execute' within 0.05s"
        " — seen: mixed(filler.state='Execute', capper.state='Idle') (no new message in 0.05s)"
    )


async def test_a_failure_names_the_member_that_never_reported(bus, line_state):
    bus.deliver(FILLER, "Execute")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(line_state).to_be("Execute", within=0.05)

    assert f"nothing arrived on {CAPPER}" in str(failure.value)


async def test_any_member_message_confirms_that_the_line_remains(bus, line_state, deliver_later):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Execute")
    deliver_later(0.02, FILLER, "Execute")

    await expect(line_state).remains(during=0.05)


async def test_one_machine_leaving_is_a_change_of_the_line(bus, line_state, deliver_later):
    bus.deliver(FILLER, "Execute")
    bus.deliver(CAPPER, "Execute")
    deliver_later(0.01, CAPPER, "Held")

    with pytest.raises(ExpectationFailed) as failure:
        await expect(line_state).remains(during=5)

    assert "it changed; seen: 'Execute' → mixed(filler.state='Execute', capper.state='Held')" in (
        str(failure.value)
    )


async def test_members_may_share_one_topic_when_a_plant_sends_one_message_per_line(bus):
    line = "acme/plant1/packaging/line1"
    members = [
        Signal(bus, line, "filler.state", path=("filler", "state")),
        Signal(bus, line, "capper.state", path=("capper", "state")),
    ]
    bus.deliver(line, {"filler": {"state": "Execute"}, "capper": {"state": "Idle"}})

    latest = Consensus(bus, members, name="line.state").latest()
    assert latest is not None
    assert repr(latest.value) == "mixed(filler.state='Execute', capper.state='Idle')"
