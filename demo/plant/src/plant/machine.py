"""What every machine does, the same for all: follow its state machine, take parameters, report.

No MQTT here, so all of it can be tested without a broker; `link.py` connects it. What makes one
machine different is its `work`: what happens in one step of time while it is producing.
"""

from plant.contracts import Unit


class Machine:
    # Counters start again from zero when the machine resets.
    counters: tuple[str, ...] = ()

    def __init__(self, unit: Unit, start: dict[str, object], acting_seconds: float):
        self.unit = unit
        self.state = unit.initial
        self.status = dict(start)
        self.acting_seconds = acting_seconds
        self._in_state_for = 0.0

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
        if done is not None and self._in_state_for >= self.acting_seconds:
            self._enter(done)
        if self.state in self.unit.roles["producing"]:
            self.work(seconds)

    def work(self, seconds: float) -> None:
        """One step of production. Each machine writes its own."""

    def report(self) -> dict[str, object]:
        """The whole state, as the contract says it goes on the wire."""
        return {"state": self.unit.states[self.state]["number"], **self.status}

    def _enter(self, state: str) -> None:
        self.state = state
        self._in_state_for = 0.0
        if state in self.unit.roles["clears_counters"]:
            self.status.update(dict.fromkeys(self.counters, 0))
