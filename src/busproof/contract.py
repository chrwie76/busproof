"""Read a line and its machine contracts, so no test ever writes a topic.

    line = read_line("demo/contracts/line.yaml")
    capper = Capper(bus, line.topics)          # line.topics("capper", "good_count") -> Address

`line.yaml` names the machines and where the line stands; each machine's AsyncAPI file says what
it publishes and what it takes. The contract is read as AsyncAPI means it, from the machine's
side: what it **sends** are its signals — one per field of the payload; what it **receives** are
its commands — one per value of an `enum` field. No channel name or topic layout is assumed.

A name the contract does not have is an error at once, listing the names it does have: a test
must not run against a guessed topic (AGENTS.md, "The contract is the truth").
"""

import re
from dataclasses import dataclass
from os.path import commonpath
from pathlib import Path

import yaml

from busproof.machines import Address


class ContractError(Exception):
    """A contract that cannot be read, or a name it does not contain."""


@dataclass(frozen=True)
class LineContract:
    name: str
    # The machines, in the order the line lists them.
    machines: list[str]
    # The unit that coordinates them, if the line has one. It has an address, but is no member.
    controller: str | None
    # (machine, signal or command) -> where it is
    addresses: dict[tuple[str, str], Address]

    @property
    def listen(self) -> str:
        """What a bus subscribes to: everything under the line, also what no contract names."""
        return commonpath([address.topic for address in self.addresses.values()]) + "/#"

    def topics(self, machine: str, name: str) -> Address:
        """Where `name` of `machine` is — a `Topics` function, to hand to a `Machine`."""
        units = [*self.machines, *([self.controller] if self.controller else [])]
        if machine not in units:
            raise ContractError(
                f"line {self.name} has no machine {machine!r}; it has: {', '.join(units)}"
            )
        if (machine, name) not in self.addresses:
            known = sorted(known for owner, known in self.addresses if owner == machine)
            raise ContractError(
                f"the contract of {machine} has no {name!r}; it has: {', '.join(known)}"
            )
        return self.addresses[(machine, name)]


def read_line(path: str | Path) -> LineContract:
    """Read `line.yaml` and every machine contract it names, relative to its folder."""
    path = Path(path)
    line = _load(path)
    addresses: dict[tuple[str, str], Address] = {}
    controller = line.get("controller")
    units = dict(line["machines"]) | ({controller["name"]: controller} if controller else {})
    for unit, entry in units.items():
        found = _read_machine(path.parent / entry["contract"], line["address"])
        addresses.update({(unit, name): address for name, address in found.items()})
    name = controller["name"] if controller else None
    return LineContract(line["name"], list(line["machines"]), name, addresses)


def _read_machine(path: Path, where: dict[str, str]) -> dict[str, Address]:
    contract = _load(path)
    found: dict[str, Address] = {}
    for operation in contract["operations"].values():
        channel = _resolve(contract, operation["channel"])
        topic = _fill(channel["address"], where, path)
        for message in channel["messages"].values():
            properties = _resolve(contract, message)["payload"].get("properties", {})
            for field, schema in properties.items():
                if operation["action"] == "send":
                    found[field] = Address(topic, (field,))
                else:
                    for command in schema.get("enum", []):
                        found[command] = Address(topic, (field,))
    return found


def _resolve(contract: dict, node: dict) -> dict:
    """Follow a local `$ref` ("#/components/messages/status"); a node without one is itself."""
    if "$ref" not in node:
        return node
    for key in node["$ref"].removeprefix("#/").split("/"):
        contract = contract[key]
    return contract


def _fill(address: str, where: dict[str, str], path: Path) -> str:
    """`{site}` and the like replaced by the line's address."""

    def value(match: re.Match[str]) -> str:
        if match[1] not in where:
            raise ContractError(f"{path.name}: line.yaml gives no value for {{{match[1]}}}")
        return where[match[1]]

    return re.sub(r"{(\w+)}", value, address)


def _load(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text())
    except OSError as error:
        raise ContractError(f"cannot read {path}: {error.strerror}") from error
