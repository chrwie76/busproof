"""The demo's contracts hold together: each machine contract is valid AsyncAPI 3.0, the state
machine is sound, every machine speaks the state numbers the state machine defines, and the
line is made of exactly these machines.

These check the files, not the plant — whether the plant keeps to them is what line-tests is for.
"""

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

from busproof import Address, read_line

CONTRACTS = Path(__file__).parents[2] / "demo" / "contracts"
ASYNCAPI = Draft7Validator(
    json.loads((Path(__file__).parent / "schemas" / "asyncapi-3.0.0.json").read_text())
)
PACKML = yaml.safe_load((CONTRACTS / "packml.yaml").read_text())
STATES: dict[str, dict] = PACKML["states"]
MACHINES = sorted((CONTRACTS / "machines").glob("*.asyncapi.yaml"))
LINE = yaml.safe_load((CONTRACTS / "line.yaml").read_text())
CONTROLLER = LINE["controller"]
# Everything that speaks on the bus: the machines, and the unit that coordinates them.
UNITS = [*MACHINES, CONTRACTS / CONTROLLER["contract"]]


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


def test_every_role_names_states_that_exist():
    for states in PACKML["roles"].values():
        assert set(states) <= set(STATES)


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


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_a_machine_contract_is_valid_asyncapi_3(path):
    contract = yaml.safe_load(path.read_text())

    errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in ASYNCAPI.iter_errors(contract)]
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_every_example_fits_its_own_payload(path):
    # An example that breaks its own contract would mislead every reader, person or agent.
    contract = yaml.safe_load(path.read_text())

    for name, message in contract["components"]["messages"].items():
        payload = Draft7Validator(message["payload"])
        for example in message.get("examples", []):
            errors = [error.message for error in payload.iter_errors(example["payload"])]
            assert not errors, f"{name}/{example['name']}: {errors}"


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_every_channel_declares_exactly_the_parameters_in_its_address(path):
    # The JSON Schema cannot see this; AsyncAPI's own parser would.
    contract = yaml.safe_load(path.read_text())

    for name, channel in contract["channels"].items():
        in_address = set(re.findall(r"{(\w+)}", channel["address"]))
        assert set(channel.get("parameters", {})) == in_address, name


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_a_machine_sends_exactly_the_state_numbers_of_the_state_machine(path):
    contract = yaml.safe_load(path.read_text())
    status = contract["components"]["messages"]["status"]["payload"]["properties"]["state"]

    assert sorted(status["enum"]) == sorted(state["number"] for state in STATES.values())


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_a_machine_takes_exactly_the_commands_of_the_state_machine(path):
    contract = yaml.safe_load(path.read_text())
    command = contract["components"]["messages"]["command"]["payload"]["properties"]["command"]
    known = {name for state in STATES.values() for name in state["commands"]}

    assert set(command["enum"]) == known


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_a_machine_contract_does_not_say_where_it_stands(path):
    contract = yaml.safe_load(path.read_text())

    assert "servers" not in contract
    for channel in contract["channels"].values():
        assert channel["address"].startswith("{enterprise}/{site}/{area}/{line}/")


# --- the line ------------------------------------------------------------------------------------


def test_the_line_names_exactly_the_machine_contracts_there_are():
    named = {CONTRACTS / machine["contract"] for machine in LINE["machines"].values()}

    assert named == set(MACHINES)


def test_each_machine_of_the_line_follows_a_state_machine_that_exists():
    for name, machine in LINE["machines"].items():
        assert (CONTRACTS / machine["states"]).is_file(), name


def test_each_machine_publishes_under_its_own_name():
    for name, machine in LINE["machines"].items():
        contract = yaml.safe_load((CONTRACTS / machine["contract"]).read_text())
        assert contract["channels"]["status"]["address"].endswith(f"/{name}"), name


def test_the_line_fills_exactly_the_parameters_of_every_address():
    for machine in LINE["machines"].values():
        contract = yaml.safe_load((CONTRACTS / machine["contract"]).read_text())
        for channel in contract["channels"].values():
            assert set(re.findall(r"{(\w+)}", channel["address"])) == set(LINE["address"])


def test_busproof_reads_the_demo_line_into_topics():
    line = read_line(CONTRACTS / "line.yaml")

    assert line.machines == ["filler", "capper", "inspector"]
    assert line.topics("capper", "good_count") == Address(
        "acme/plant1/packaging/line1/capper", ("good_count",)
    )
    assert line.topics("inspector", "Start") == Address(
        "acme/plant1/packaging/line1/inspector/cmd", ("command",)
    )


# --- the controller ------------------------------------------------------------------------------


def test_a_bottle_travels_to_every_machine_after_the_first_in_their_order():
    assert [leg["to"] for leg in LINE["transport"]] == list(LINE["machines"])[1:]


def test_the_controller_starts_and_stops_exactly_the_machines_of_the_line():
    assert sorted(CONTROLLER["start_order"]) == sorted(LINE["machines"])
    assert sorted(CONTROLLER["stop_order"]) == sorted(LINE["machines"])


def test_the_line_starts_from_its_end_and_stops_from_its_beginning():
    bottle_order = list(LINE["machines"])

    assert CONTROLLER["start_order"] == bottle_order[::-1]
    assert CONTROLLER["stop_order"] == bottle_order


def test_the_controllers_reaction_to_a_fault_is_a_command_of_the_state_machine():
    known = {name for state in STATES.values() for name in state["commands"]}

    assert CONTROLLER["on_machine_fault"] in known


def test_the_controller_follows_a_state_machine_that_exists():
    assert (CONTRACTS / CONTROLLER["states"]).is_file()


def test_the_controller_fills_the_same_address_as_the_machines():
    contract = yaml.safe_load((CONTRACTS / CONTROLLER["contract"]).read_text())

    for channel in contract["channels"].values():
        assert set(re.findall(r"{(\w+)}", channel["address"])) == set(LINE["address"])
    assert contract["channels"]["status"]["address"].endswith(f"/{CONTROLLER['name']}")


@pytest.mark.parametrize("path", UNITS, ids=lambda path: path.name)
def test_every_unit_can_say_that_it_is_gone(path):
    contract = yaml.safe_load(path.read_text())
    sent = [
        operation["channel"]["$ref"]
        for operation in contract["operations"].values()
        if operation["action"] == "send"
    ]

    assert "#/channels/online" in sent
