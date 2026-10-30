"""The SCU, the central unit of the line. It follows the same state machine as a machine, but its
acting states end when the machines have got there, not when a time is up.

It knows the machines only from what they report, so it notices a machine that was stopped behind
its back, failed, or went silent. It counts no product.
"""

from plant.contracts import Plan, Unit
from plant.machine import Machine


class Scu(Machine):
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
        self._outbox: list[tuple[str, dict]] = []

    def listens_to(self) -> list[str]:
        topics = super().listens_to()
        for machine in self.plan.machines.values():
            topics += [machine.status_topic, machine.online_topic]
        return topics

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
        super().hear(topic, values)

    def take(self, command: str) -> bool:
        taken = super().take(command)
        if taken:
            self._pass_on(command)
        return taken

    def outgoing(self) -> list[tuple[str, dict]]:
        messages, self._outbox = self._outbox, []
        return messages

    def tick(self, seconds: float) -> None:
        for name in self._silent_for:
            self._silent_for[name] += seconds
        if self.state in self.unit.roles["producing"]:
            self._watch_machines()
        super().tick(seconds)

    def work(self, seconds: float) -> None:
        """The SCU produces nothing itself."""

    def _pass_on(self, command: str) -> None:
        order = {"Start": self.plan.start_order, "Stop": self.plan.stop_order}
        for name in order.get(command, self.plan.stop_order):
            self._outbox.append((self.plan.machines[name].command_topic, {"command": command}))

    def _watch_machines(self) -> None:
        """A running line needs every machine: the first that is not running makes it react."""
        for name in self.plan.machines:
            running = self.machine_states.get(name) in self.unit.roles["producing"]
            if name in self.gone or not running or self._is_silent(name):
                self.status["faulted_machine"] = name
                self.take(self.plan.on_machine_fault)
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

    def _enter(self, state: str) -> None:
        super()._enter(state)
        if state in self.unit.roles["clears_counters"]:
            self.status["faulted_machine"] = None

    @staticmethod
    def _state_named(machine: Unit, number: int) -> str:
        for name, state in machine.states.items():
            if state["number"] == number:
                return name
        raise ValueError(f"no state has the number {number}")
