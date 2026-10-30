"""The inspection station at the end of the line: measures how full each bottle is, passes the
good ones and rejects the rest. A fault at the start of the line shows here, seconds later."""

from plant.machine import Machine


class Inspector(Machine):
    counters = ("pass_count", "reject_count")

    def judge(self, bottle_fill_level: float) -> str:
        minimum = self.status["min_fill_level"]
        assert isinstance(minimum, int | float)
        self.status["last_fill_level"] = bottle_fill_level
        if bottle_fill_level >= minimum:
            self._add("pass_count", 1)
            return "pass"
        self._add("reject_count", 1)
        return "reject"
