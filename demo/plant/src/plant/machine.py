"""What every unit does, the same for all: follow its state machine, take parameters, report.

No MQTT here, so all of it can be tested without a broker; `link.py` connects it. What makes one
machine different is its `work`: what happens in one step of time while it is producing.
"""

import logging

from plant.contracts import Unit

logger = logging.getLogger("plant")


class Machine:
    # Counters start again from zero when the machine resets.
    counters: tuple[str, ...] = ()

    def __init__(self, unit: Unit, start: dict[str, object], acting_seconds: float):
        self.unit = unit
        self.state = unit.initial
        self.status = dict(start)
        self.acting_seconds = acting_seconds
        self._in_state_for = 0.0
        self._bottles_due = 0.0  # a bottle takes longer than a step: the fraction waits here
        self._outbox: list[tuple[str, dict]] = []

    def listens_to(self) -> list[str]:
        """The topics this unit acts on."""
        optional = [self.unit.settings_topic, self.unit.unit_topic]
        return [self.unit.command_topic, *[topic for topic in optional if topic]]

    def hear(self, topic: str, values: dict) -> None:
        """Act on one message from the bus. Raises on one that makes no sense."""
        if topic == self.unit.command_topic:
            taken = self.take(values["command"])
            logger.info("command %s, now %s: %s", values["command"], self.state, taken)
        elif topic == self.unit.settings_topic:
            logger.info("parameters taken: %s", self.change(values))
        elif topic == self.unit.unit_topic:
            self._arrived(values)

    def outgoing(self) -> list[tuple[str, dict]]:
        """Messages to send now, for other units."""
        messages, self._outbox = self._outbox, []
        return messages

    def take(self, command: str) -> bool:
        """Follow `command` if this state accepts it. Returns whether it did."""
        target = self.unit.states[self.state]["commands"].get(command)
        if target is None:
            return False
        self._enter(target)
        return True

    def change(self, values: dict[str, object]) -> list[str]:
        """Take the parameters the contract knows, within its limits. Returns those it took."""
        taken = []
        for name, value in values.items():
            limits = self.unit.settings.get(name)
            if limits is None or not isinstance(value, int | float) or isinstance(value, bool):
                continue
            if limits["minimum"] <= value <= limits["maximum"]:
                self.status[name] = value
                taken.append(name)
        return taken

    def tick(self, seconds: float) -> None:
        """One step of time: an acting state may finish, a producing machine works."""
        self._in_state_for += seconds
        done = self.unit.states[self.state].get("done")
        if done is not None and self._finished_acting(done):
            self._enter(done)
        if self.state in self.unit.roles["producing"]:
            self.work(seconds)

    def work(self, seconds: float) -> None:
        """One step of production. Each machine writes its own."""

    def judge(self, bottle_fill_level: float) -> str:
        """A bottle is here: do the station's work, count it, and return the result."""
        return "pass"

    def report(self) -> dict[str, object]:
        """The whole state, as the contract says it goes on the wire."""
        return {"state": self.unit.states[self.state]["number"], **self.status}

    def _arrived(self, values: dict) -> None:
        unit, level = values["unit"], values["bottle_fill_level"]
        producing = self.state in self.unit.roles["producing"]
        self._report_unit(unit, level, self.judge(level) if producing else "refused")

    def _report_unit(self, unit: str, level: float, result: str) -> None:
        assert self.unit.unit_done_topic is not None
        message = {"unit": unit, "bottle_fill_level": level, "result": result}
        self._outbox.append((self.unit.unit_done_topic, message))

    def _finished_acting(self, done: str) -> bool:
        return self._in_state_for >= self.acting_seconds

    def _count_bottles(self, seconds: float) -> int:
        """How many bottles this step finishes at the speed set."""
        speed = self.status["speed"]
        assert isinstance(speed, int | float)
        self._bottles_due += speed / 60 * seconds
        finished = int(self._bottles_due)
        self._bottles_due -= finished
        return finished

    def _add(self, counter: str, amount: int) -> None:
        count = self.status[counter]
        assert isinstance(count, int)
        self.status[counter] = count + amount

    def _is_empty(self, supply: str) -> bool:
        level = self.status[supply]
        assert isinstance(level, int | float)
        return level <= 0

    def _enter(self, state: str) -> None:
        self.state = state
        self._in_state_for = 0.0
        if state in self.unit.roles["clears_counters"]:
            self.status.update(dict.fromkeys(self.counters, 0))
