"""The capping station: closes bottles, counts the good ones."""

from plant.machine import Machine


class Capper(Machine):
    counters = ("good_count", "reject_count")

    def work(self, seconds: float) -> None:
        self._add("good_count", self._count_bottles(seconds))
        self.status["torque"] = self.status["torque_target"]
