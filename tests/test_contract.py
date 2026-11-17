"""The contract is read into an address book, so no test writes a topic — and a name the
contract does not have fails at once, saying which names it has."""

from pathlib import Path

import pytest
import yaml

from busproof import Address, ContractError, Machine, read_line

LINE = {
    "name": "line9",
    "address": {"site": "plant9", "line": "line9"},
    "machines": {
        "mixer": {"contract": "machines/mixer.asyncapi.yaml"},
        "oven": {"contract": "machines/oven.asyncapi.yaml"},
    },
}
BOSS = {"name": "boss", "contract": "machines/boss.asyncapi.yaml"}


def machine_contract(name: str) -> dict:
    """A small AsyncAPI 3.0 contract: the machine sends its state, and takes two commands. The
    channel names are made up on purpose: the reader must not depend on them."""
    return {
        "asyncapi": "3.0.0",
        "info": {"title": name, "version": "1.0.0"},
        "channels": {
            "out": {
                "address": f"{{site}}/{{line}}/{name}",
                "messages": {"m": {"$ref": "#/components/messages/report"}},
            },
            "in": {
                "address": f"{{site}}/{{line}}/{name}/do",
                "messages": {
                    "m": {
                        "payload": {"properties": {"order": {"enum": ["Go", "Halt"]}, "heat": {}}}
                    }
                },
            },
        },
        "operations": {
            "report": {"action": "send", "channel": {"$ref": "#/channels/out"}},
            "obey": {"action": "receive", "channel": {"$ref": "#/channels/in"}},
        },
        "components": {
            "messages": {
                "report": {"payload": {"properties": {"state": {}, "temperature": {}}}},
            }
        },
    }


@pytest.fixture
def line_file(tmp_path: Path) -> Path:
    (tmp_path / "machines").mkdir()
    for name in [*LINE["machines"], BOSS["name"]]:
        contract = tmp_path / "machines" / f"{name}.asyncapi.yaml"
        contract.write_text(yaml.safe_dump(machine_contract(name)))
    path = tmp_path / "line.yaml"
    path.write_text(yaml.safe_dump(LINE))
    return path


def test_what_a_machine_sends_becomes_a_signal_in_its_payload(line_file):
    line = read_line(line_file)

    assert line.topics("oven", "temperature") == Address("plant9/line9/oven", ("temperature",))


def test_what_a_machine_receives_becomes_a_command_at_its_field(line_file):
    line = read_line(line_file)

    assert line.topics("mixer", "Halt") == Address("plant9/line9/mixer/do", ("order",))


def test_the_line_keeps_its_name_and_the_order_of_its_machines(line_file):
    line = read_line(line_file)

    assert (line.name, line.machines) == ("line9", ["mixer", "oven"])


def test_what_a_machine_receives_without_an_enum_becomes_a_parameter(line_file):
    line = read_line(line_file)

    assert line.topics("oven", "set heat") == Address("plant9/line9/oven/do", ("heat",))


async def test_a_machine_sets_a_parameter_where_the_contract_says(line_file, bus):
    oven = Machine(bus, read_line(line_file).topics, "oven")

    await oven.set(heat=180)

    assert [(message.topic, message.value) for message in bus.sent] == [
        ("plant9/line9/oven/do", {"heat": 180})
    ]


async def test_a_parameter_the_contract_does_not_have_fails_and_sends_nothing(line_file, bus):
    oven = Machine(bus, read_line(line_file).topics, "oven")

    with pytest.raises(ContractError, match="has no 'set colour'"):
        await oven.set(colour="red")

    assert bus.sent == []


def test_a_line_may_name_a_unit_that_coordinates_it(line_file):
    line = yaml.safe_load(line_file.read_text())
    line["controller"] = BOSS
    line_file.write_text(yaml.safe_dump(line))

    contract = read_line(line_file)

    assert contract.controller == "boss"
    assert contract.machines == ["mixer", "oven"], "the coordinator is no member of the line"
    assert contract.topics("boss", "Go") == Address("plant9/line9/boss/do", ("order",))


def test_a_line_without_one_has_none(line_file):
    assert read_line(line_file).controller is None


def test_a_bus_listens_to_everything_under_the_line(line_file):
    assert read_line(line_file).listen == "plant9/line9/#"


async def test_a_machine_built_on_the_contract_sends_and_reads_where_it_says(line_file, bus):
    oven = Machine(bus, read_line(line_file).topics, "oven")

    await oven.send("Go")

    assert [(message.topic, message.value) for message in bus.sent] == [
        ("plant9/line9/oven/do", {"order": "Go"})
    ]
    assert (oven.state.topic, oven.state.path) == ("plant9/line9/oven", ("state",))


def test_a_name_the_contract_does_not_have_fails_and_lists_the_ones_it_has(line_file):
    line = read_line(line_file)

    with pytest.raises(ContractError) as error:
        line.topics("oven", "temprature")

    assert str(error.value) == (
        "the contract of oven has no 'temprature'; it has: Go, Halt, set heat, state, temperature"
    )


def test_a_machine_the_line_does_not_have_fails_and_lists_the_ones_it_has(line_file):
    with pytest.raises(ContractError) as error:
        read_line(line_file).topics("mixr", "state")

    assert str(error.value) == "line line9 has no machine 'mixr'; it has: mixer, oven"


def test_an_address_part_the_line_does_not_give_fails(line_file):
    line = yaml.safe_load(line_file.read_text())
    del line["address"]["site"]
    line_file.write_text(yaml.safe_dump(line))

    with pytest.raises(ContractError, match=r"line.yaml gives no value for {site}"):
        read_line(line_file)


def test_a_missing_contract_file_is_named(line_file):
    (line_file.parent / "machines" / "oven.asyncapi.yaml").unlink()

    with pytest.raises(ContractError, match="cannot read .*oven.asyncapi.yaml"):
        read_line(line_file)
