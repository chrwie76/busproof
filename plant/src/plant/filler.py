"""The filling station, where bottles begin: fills them to the level set, using up empty bottles
and its tank. When either is empty it holds, as PackML means Hold: a reason inside the machine."""

from plant.contracts import Unit
from plant.machine import Machine

TANK_PER_FULL_BOTTLE = 0.01  # percent of the tank


class Filler(Machine):
    counters = ("filled_count",)

    def __init__(self, unit: Unit, start: dict[str, object], acting_seconds: float):
        super().__init__(unit, start, acting_seconds)
        self._made = 0

    def work(self, seconds: float) -> None:
        for _ in range(self._count_bottles(seconds)):
            if self._is_empty("bottle_supply") or self._is_empty("tank_level"):
                self.take("Hold")
                return
            self._fill_one()
        if self._is_empty("bottle_supply") or self._is_empty("tank_level"):
            self.take("Hold")

    def _fill_one(self) -> None:
        level = self.status["fill_target"]
        tank_level = self.status["tank_level"]
        assert isinstance(level, int | float) and isinstance(tank_level, int | float)
        self._made += 1
        self._add("filled_count", 1)
        self._add("bottle_supply", -1)
        self.status["fill_level"] = level
        self.status["tank_level"] = max(0.0, tank_level - TANK_PER_FULL_BOTTLE * level / 100)
        self._report_unit(f"bottle-{self._made}", level, "pass")
