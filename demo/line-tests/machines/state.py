"""What the state numbers on the wire mean, as `../contracts/packml.yaml` defines them."""

from enum import IntEnum


class State(IntEnum):
    CLEARING = 1
    STOPPED = 2
    STARTING = 3
    IDLE = 4
    EXECUTE = 6
    STOPPING = 7
    ABORTING = 8
    ABORTED = 9
    HOLDING = 10
    HELD = 11
    UNHOLDING = 12
    RESETTING = 15
