"""The demo's contracts hold together: each machine contract is valid AsyncAPI 3.0, the state
machine is sound, and every machine speaks the state numbers the state machine defines.

These check the files, not the plant — whether the plant keeps to them is what line-tests is for.
"""

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

CONTRACTS = Path(__file__).parents[2] / "demo" / "contracts"
ASYNCAPI = Draft7Validator(
    json.loads((Path(__file__).parent / "schemas" / "asyncapi-3.0.0.json").read_text())
)
PACKML = yaml.safe_load((CONTRACTS / "packml.yaml").read_text())
STATES: dict[str, dict] = PACKML["states"]
MACHINES = sorted((CONTRACTS / "machines").glob("*.asyncapi.yaml"))


def test_every_state_has_its_own_number():
    numbers = [state["number"] for state in STATES.values()]
    assert len(numbers) == len(set(numbers))


def test_every_transition_leads_to_a_state_that_exists():
    targets = [PACKML["initial"]]
    for state in STATES.values():
        targets += list(state["commands"].values())
        targets += [state["done"]] if "done" in state else []
    assert set(targets) <= set(STATES)


def test_exactly_the_acting_states_finish_on_their_own():
    for name, state in STATES.items():
        assert ("done" in state) == name.endswith("ing"), name


def test_every_state_can_be_reached_from_the_initial_one():
    reached, todo = set(), [PACKML["initial"]]
    while todo:
        name = todo.pop()
        if name not in reached:
            reached.add(name)
            state = STATES[name]
            todo += list(state["commands"].values()) + ([state["done"]] if "done" in state else [])
    assert reached == set(STATES)


def test_there_is_a_machine_contract():
    assert MACHINES


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_a_machine_contract_is_valid_asyncapi_3(path):
    contract = yaml.safe_load(path.read_text())

    errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in ASYNCAPI.iter_errors(contract)]
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_every_example_fits_its_own_payload(path):
    # An example that breaks its own contract would mislead every reader, person or agent.
    contract = yaml.safe_load(path.read_text())

    for name, message in contract["components"]["messages"].items():
        payload = Draft7Validator(message["payload"])
        for example in message.get("examples", []):
            errors = [error.message for error in payload.iter_errors(example["payload"])]
            assert not errors, f"{name}/{example['name']}: {errors}"


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_every_channel_declares_exactly_the_parameters_in_its_address(path):
    # The JSON Schema cannot see this; AsyncAPI's own parser would.
    contract = yaml.safe_load(path.read_text())

    for name, channel in contract["channels"].items():
        in_address = set(re.findall(r"{(\w+)}", channel["address"]))
        assert set(channel.get("parameters", {})) == in_address, name


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_a_machine_sends_exactly_the_state_numbers_of_the_state_machine(path):
    contract = yaml.safe_load(path.read_text())
    status = contract["components"]["messages"]["status"]["payload"]["properties"]["state"]

    assert sorted(status["enum"]) == sorted(state["number"] for state in STATES.values())


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_a_machine_takes_exactly_the_commands_of_the_state_machine(path):
    contract = yaml.safe_load(path.read_text())
    command = contract["components"]["messages"]["command"]["payload"]["properties"]["command"]
    known = {name for state in STATES.values() for name in state["commands"]}

    assert set(command["enum"]) == known


@pytest.mark.parametrize("path", MACHINES, ids=lambda path: path.name)
def test_a_machine_contract_does_not_say_where_it_stands(path):
    contract = yaml.safe_load(path.read_text())

    assert "servers" not in contract
    for channel in contract["channels"].values():
        assert channel["address"].startswith("{enterprise}/{site}/{area}/{line}/")
