"""The SCU, the central unit of the line. It follows the same state machine as a machine, but its
acting states end when the machines have got there, not when a time is up.

It knows the machines only from what they report, so it notices a machine that was stopped behind
its back, failed, or went silent. It plays the transport too: it knows where each bottle is and
when it arrives, and each station says what became of it. It counts no product, only what it is
alone in knowing: bottles on their way, and bottles lost.
"""

from dataclasses import dataclass

from plant.contracts import Plan, Unit
from plant.machine import Machine


@dataclass
class Bottle:
    unit: str
    level: float
    to: str
    seconds_left: float


class Scu(Machine):
    counters = ("lost",)

    def __init__(
        self,
        unit: Unit,
        plan: Plan,
        start: dict[str, object],
        acting_seconds: float,
        silence_seconds: float,
    ):
        super().__init__(unit, start, acting_seconds)
        self.plan = plan
        self.silence_seconds = silence_seconds
        self.machine_states: dict[str, str] = {}
        self.gone: set[str] = set()
        self._silent_for = dict.fromkeys(plan.machines, 0.0)
        self._belt: list[Bottle] = []
        self._at_station: dict[str, str] = {}  # bottle -> the station whose answer is awaited
        self._still_to_stop: list[str] = []

    def listens_to(self) -> list[str]:
        topics = super().listens_to()
        for machine in self.plan.machines.values():
            topics += [machine.status_topic, machine.online_topic, machine.unit_done_topic or ""]
        return [topic for topic in topics if topic]

    def hear(self, topic: str, values: dict) -> None:
        for name, machine in self.plan.machines.items():
            if topic == machine.status_topic:
                self.machine_states[name] = self._state_named(machine, values["state"])
                self._silent_for[name] = 0.0
                return
            if topic == machine.online_topic:
                (self.gone.discard if values["online"] else self.gone.add)(name)
                self._silent_for[name] = 0.0
                return
            if topic == machine.unit_done_topic:
                self._unit_done(name, values)
                return
        super().hear(topic, values)

    def take(self, command: str) -> bool:
        was_running = self.state in self.unit.roles["producing"]
        taken = super().take(command)
        if taken:
            # A new order: what made the SCU react before is no longer the point.
            self.status["faulted_machine"] = None
            self._still_to_stop = []
            if self.state in self.unit.roles["drops_units"]:
                self._lose_everything()
            self._pass_on(command, was_running)
        return taken

    def tick(self, seconds: float) -> None:
        for name in self._silent_for:
            self._silent_for[name] += seconds
        self._give_up_on_stations_that_cannot_answer()
        if self.state in self.unit.roles["producing"]:
            self._watch_machines()
        if self.state in self.unit.roles["producing"] or self._still_to_stop:
            self._move_belt(seconds)
        self._stop_the_rest_once_empty()
        self.status["in_transit"] = len(self._belt) + len(self._at_station)
        super().tick(seconds)

    def _pass_on(self, command: str, was_running: bool) -> None:
        if command == "Start":
            order = self.plan.start_order
        elif command == "Stop" and was_running:
            # Only the first: the rest keep working until the belt has run empty.
            order = self.plan.stop_order[:1]
            self._still_to_stop = self.plan.stop_order[1:]
        else:
            if command == "Stop":
                self._lose_everything()  # the belt stood still: nothing will bring these home
            order = self.plan.stop_order
        self._send_to(order, command)

    def _send_to(self, machines: list[str], command: str) -> None:
        for name in machines:
            self._outbox.append((self.plan.machines[name].command_topic, {"command": command}))

    def _stop_the_rest_once_empty(self) -> None:
        if not self._still_to_stop or self._belt or self._at_station:
            return
        first = self.plan.stop_order[0]
        if self.machine_states.get(first) not in self.unit.roles["producing"]:
            self._send_to(self._still_to_stop, "Stop")
            self._still_to_stop = []

    def _watch_machines(self) -> None:
        """A running line needs every machine: the first that is not running makes it react."""
        for name in self.plan.machines:
            running = self.machine_states.get(name) in self.unit.roles["producing"]
            if name in self.gone or not running or self._is_silent(name):
                self.take(self.plan.on_machine_fault)
                self.status["faulted_machine"] = name
                return

    def _is_silent(self, name: str) -> bool:
        return self._silent_for[name] > self.silence_seconds

    def _finished_acting(self, done: str) -> bool:
        """Finished when every machine it can still count on has got there, and at least one has:
        with no machine left, a claim like "the line is in Execute" would be about nothing. A
        machine merely silent still counts: what it last said does not show it got there."""
        counted = [
            self.machine_states.get(name)
            for name in self.plan.machines
            if name not in self.gone and name != self.status["faulted_machine"]
        ]
        return bool(counted) and all(state == done for state in counted)

    # --- the transport ---------------------------------------------------------------------------

    def _unit_done(self, station: str, values: dict) -> None:
        unit, level, result = values["unit"], values["bottle_fill_level"], values["result"]
        names = list(self.plan.machines)
        if station != names[0] and self._at_station.pop(unit, None) is None:
            return  # no longer expected: it was given up for lost
        if result == "refused":
            self._add("lost", 1)
        following = names[names.index(station) + 1 :]
        if result == "pass" and following:
            self._belt.append(Bottle(unit, level, following[0], self.plan.transport[following[0]]))

    def _move_belt(self, seconds: float) -> None:
        for bottle in list(self._belt):
            bottle.seconds_left -= seconds
            if bottle.seconds_left <= 0:
                self._belt.remove(bottle)
                self._arrive(bottle)

    def _arrive(self, bottle: Bottle) -> None:
        if self._cannot_answer(bottle.to):
            self._add("lost", 1)
            return
        self._at_station[bottle.unit] = bottle.to
        topic = self.plan.machines[bottle.to].unit_topic
        assert topic is not None
        self._outbox.append((topic, {"unit": bottle.unit, "bottle_fill_level": bottle.level}))

    def _give_up_on_stations_that_cannot_answer(self) -> None:
        for unit, station in list(self._at_station.items()):
            if self._cannot_answer(station):
                del self._at_station[unit]
                self._add("lost", 1)

    def _cannot_answer(self, station: str) -> bool:
        return station in self.gone or self._is_silent(station)

    def _lose_everything(self) -> None:
        self._add("lost", len(self._belt) + len(self._at_station))
        self._belt.clear()
        self._at_station.clear()

    @staticmethod
    def _state_named(machine: Unit, number: int) -> str:
        for name, state in machine.states.items():
            if state["number"] == number:
                return name
        raise ValueError(f"no state has the number {number}")
