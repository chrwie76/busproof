"""A stand-in for the plant, until the real one exists (M2): lets the tests run with no broker.

It reads the same contracts the real plant will, and plays each machine over the fake bus: takes
the commands its state accepts, leaves acting states on its own, counts while in Execute, and
reports its whole state at a steady pace. It is no simulation — no bottle travels, nothing can
go wrong — so a green run here proves the test project's wiring, not a plant.
"""

import asyncio
from pathlib import Path

import yaml

from busproof import FakeBus, LineContract

TICK = 0.01  # seconds between two reports


class StandInMachine:
    def __init__(self, status: dict[str, object], states: dict[str, dict], initial: str):
        self.status = status
        self.states = states
        self.state = initial

    def take(self, command: str) -> None:
        self.state = self.states[self.state]["commands"].get(command, self.state)

    def tick(self, counters: list[str]) -> dict[str, object]:
        """One step of time; returns the whole state to report."""
        self.state = self.states[self.state].get("done", self.state)
        if self.state == "Execute":
            for counter in counters:
                self.status[counter] = int(str(self.status[counter])) + 1
        return {"state": self.states[self.state]["number"], **self.status}


# What each machine reports besides its state, and which of it counts up while running.
MACHINES: dict[str, tuple[dict[str, object], list[str]]] = {
    "filler": (
        {
            "filled_count": 0,
            "fill_level": 98.0,
            "tank_level": 80.0,
            "speed": 60.0,
            "fill_target": 98.0,
        },
        ["filled_count"],
    ),
    "capper": (
        {"good_count": 0, "reject_count": 0, "torque": 2.0, "speed": 60.0, "torque_target": 2.0},
        ["good_count"],
    ),
    "inspector": (
        {"pass_count": 0, "reject_count": 0, "last_fill_level": 98.0, "min_fill_level": 90.0},
        ["pass_count"],
    ),
}


async def run_stand_in(bus: FakeBus, contract: LineContract, line_file: Path) -> None:
    line = yaml.safe_load(line_file.read_text())
    machines: dict[str, StandInMachine] = {}
    for name in contract.machines:
        packml = yaml.safe_load((line_file.parent / line["machines"][name]["states"]).read_text())
        machines[name] = StandInMachine(
            dict(MACHINES[name][0]), packml["states"], packml["initial"]
        )
    by_command_topic = {contract.topics(name, "Start").topic: name for name in contract.machines}

    seen = 0
    while True:
        for message in bus.recorder.messages(since=seen):
            if message.direction == "sent" and message.topic in by_command_topic:
                command = message.value
                assert isinstance(command, dict)
                machines[by_command_topic[message.topic]].take(command["command"])
        seen = len(bus.recorder)
        for name, machine in machines.items():
            report = machine.tick(MACHINES[name][1])
            bus.deliver(contract.topics(name, "state").topic, report)
        await asyncio.sleep(TICK)
