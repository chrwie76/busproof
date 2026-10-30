"""The capping station: closes bottles, counts the good ones."""

from plant.contracts import Unit
from plant.machine import Machine


class Capper(Machine):
    counters = ("good_count", "reject_count")

    def __init__(self, unit: Unit, start: dict[str, object], acting_seconds: float):
        super().__init__(unit, start, acting_seconds)
        self._bottles_due = 0.0  # a bottle takes longer than a step: the fraction waits here

    def work(self, seconds: float) -> None:
        speed = self.status["speed"]
        assert isinstance(speed, int | float)
        self._bottles_due += speed / 60 * seconds
        finished = int(self._bottles_due)
        self._bottles_due -= finished
        good_count = self.status["good_count"]
        assert isinstance(good_count, int)
        self.status["good_count"] = good_count + finished
        self.status["torque"] = self.status["torque_target"]
