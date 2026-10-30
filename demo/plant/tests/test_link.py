"""What arrives on the bus reaches the machine, and nonsense changes nothing."""

from pathlib import Path

import pytest

from plant.capper import Capper
from plant.contracts import read_unit
from plant.link import receive

CONTRACTS = Path(__file__).parents[2] / "contracts"
START: dict[str, object] = {
    "good_count": 0,
    "reject_count": 0,
    "torque": 0.0,
    "cap_supply": 100,
    "torque_target": 2.0,
}


@pytest.fixture
def capper() -> Capper:
    return Capper(read_unit(CONTRACTS, "capper"), START, 0.5)


def test_a_command_reaches_the_machine(capper: Capper):
    receive(capper, capper.unit.command_topic, b'{"command": "Reset"}')

    assert capper.state == "Resetting"


def test_parameters_reach_the_machine(capper: Capper):
    assert capper.unit.settings_topic is not None
    receive(capper, capper.unit.settings_topic, b'{"torque_target": 2.2}')

    assert capper.status["torque_target"] == 2.2


@pytest.mark.parametrize(
    "payload",
    [
        b"garbage",
        b'{"order": "Reset"}',
        b'"Reset"',
        b"[1, 2]",
        b"7",
        b"null",
        None,
        b'{"command": []}',
    ],
)
def test_a_message_that_makes_no_sense_changes_nothing_on_any_topic(
    capper: Capper, payload: object
):
    for topic in capper.listens_to():
        receive(capper, topic, payload)

    assert capper.state == "Stopped"
    assert capper.fault is None
    assert capper.status == START


def test_a_fault_that_does_not_exist_is_refused(capper: Capper):
    receive(capper, capper.fault_topic, b'{"fault": "no_such_fault"}')

    assert capper.fault is None


def test_a_fault_can_be_switched_on_and_off(capper: Capper):
    receive(capper, capper.fault_topic, b'{"fault": "silent"}')
    assert capper.fault == "silent"

    receive(capper, capper.fault_topic, b'{"fault": null}')
    assert capper.fault is None
