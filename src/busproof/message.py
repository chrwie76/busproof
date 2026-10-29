"""One message on a bus, as the recorder keeps it."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

# Received from the system, or sent to it by the test. Both belong to the evidence: what the
# test did is as much a part of the story as what the system answered.
Direction = Literal["received", "sent"]


@dataclass(frozen=True)
class Message:
    """A value on a topic, and the moment it was seen.

    `at` counts seconds since the recording started, on a monotonic clock: it orders messages and
    measures latencies, and it cannot jump when the computer's clock is adjusted.
    """

    topic: str
    value: object
    at: float
    direction: Direction = "received"


def show(value: object) -> str:
    """A value as a failure message writes it: `'Execute'`, `120` — and an enum member with the
    number that was on the wire, `EXECUTE (6)`, so both the meaning and the evidence show."""
    if isinstance(value, Enum):
        return f"{value.name} ({value.value!r})"
    return repr(value)
