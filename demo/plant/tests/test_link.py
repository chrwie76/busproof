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
    "speed": 60.0,
    "torque_target": 2.0,
}


@pytest.fixture
def capper() -> Capper:
    return Capper(read_unit(CONTRACTS, "capper"), START, 0.5)


def test_a_command_reaches_the_machine(capper: Capper):
    receive(capper, capper.unit.command_topic, b'{"command": "Reset"}')

    assert capper.state == "Resetting"


def test_parameters_reach_the_machine(capper: Capper):
    receive(capper, capper.unit.settings_topic, b'{"speed": 30.0}')

    assert capper.status["speed"] == 30.0


@pytest.mark.parametrize("payload", [b"garbage", b'{"order": "Reset"}', b'"Reset"', None])
def test_a_message_that_makes_no_sense_changes_nothing(capper: Capper, payload: object):
    receive(capper, capper.unit.command_topic, payload)

    assert capper.state == "Stopped"
