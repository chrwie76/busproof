"""A signal is a handle on a value the system publishes — not the value itself.

Like a Playwright locator, a signal reads nothing when it is created. `expect(signal)` reads it,
and keeps reading until the system agrees or the time is up. A value read once and then
compared is a race against an asynchronous system.
"""

from dataclasses import dataclass

from busproof.bus import Bus


@dataclass(frozen=True)
class Signal:
    bus: Bus
    topic: str
    # How a failure message names the signal: "capper.good_count", never the topic.
    name: str
