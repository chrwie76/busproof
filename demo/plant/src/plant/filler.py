"""The filling station: fills bottles to the level set, from a tank that runs down."""

from plant.machine import Machine

TANK_PER_BOTTLE = 0.01  # percent of the tank


class Filler(Machine):
    counters = ("filled_count",)

    def work(self, seconds: float) -> None:
        finished = self._count_bottles(seconds)
        self._add("filled_count", finished)
        self.status["fill_level"] = self.status["fill_target"]
        tank_level = self.status["tank_level"]
        assert isinstance(tank_level, int | float)
        self.status["tank_level"] = max(0.0, tank_level - finished * TANK_PER_BOTTLE)
