"""The inspection station at the end of the line. It judges bottles as they arrive, and none
arrive yet: the transport comes in the next step."""

from plant.machine import Machine


class Inspector(Machine):
    counters = ("pass_count", "reject_count")
