"""The capping station: closes each bottle that arrives, with one cap, and counts good and bad.
When the caps run out it holds."""

from plant.machine import Machine

GOOD_TORQUE = (1.5, 2.5)  # Nm: a cap closed outside this is a reject


class Capper(Machine):
    counters = ("good_count", "reject_count")

    def work(self, seconds: float) -> None:
        if self._is_empty("cap_supply"):
            self.take("Hold")

    def judge(self, bottle_fill_level: float) -> str:
        torque = self.status["torque_target"]
        assert isinstance(torque, int | float)
        self._add("cap_supply", -1)
        self.status["torque"] = torque
        if GOOD_TORQUE[0] <= torque <= GOOD_TORQUE[1]:
            self._add("good_count", 1)
            return "pass"
        self._add("reject_count", 1)
        return "reject"
