"""A signal is a handle on a value the system publishes — not the value itself.

Like a Playwright locator, a signal reads nothing when it is created. `expect(signal)` reads it,
and keeps reading until the system agrees or the time is up. A value read once and then
compared is a race against an asynchronous system.

Two kinds: a `Signal` is one topic; a `Consensus` is what several signals agree on, such as the
state of a line made of machines.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from busproof.bus import Bus
from busproof.message import Message


@dataclass(frozen=True)
class Signal:
    bus: Bus
    topic: str
    # How a failure message names the signal: "capper.good_count", never the topic.
    name: str

    def latest(self) -> Message | None:
        """The newest message received for this signal, or None."""
        return self.bus.recorder.latest(self.topic)

    def fresh(self, since: int) -> list[Message]:
        """Messages received for this signal after the first `since` of the recording."""
        messages = self.bus.recorder.messages(self.topic, since=since)
        return [message for message in messages if message.direction == "received"]

    def silent(self) -> str:
        """Where to look when nothing arrived: the topic, since a misspelt one is likely."""
        return self.topic


@dataclass(frozen=True)
class Mixed:
    """The value of a consensus whose members disagree — it has no value of its own."""

    values: tuple[tuple[str, object], ...]

    def __repr__(self) -> str:
        return "mixed(" + ", ".join(f"{name}={value!r}" for name, value in self.values) + ")"


class Consensus:
    """The value all `members` agree on; `Mixed` while they differ.

    A line is `Execute` only when every machine is — one member never speaks for all. Until
    every member has reported, the consensus has no value at all. Each message of a member is a
    fresh message of the consensus, so `remains` is confirmed by any of them.
    """

    def __init__(self, bus: Bus, members: Sequence[Signal], name: str):
        self.bus = bus
        self.members = list(members)
        self.name = name

    def latest(self) -> Message | None:
        history = self._history()
        return history[-1][1] if history else None

    def fresh(self, since: int) -> list[Message]:
        return [message for index, message in self._history() if index >= since]

    def silent(self) -> str:
        """The members that never reported — or all of them, if each one has."""
        quiet = [member.topic for member in self.members if member.latest() is None]
        return ", ".join(quiet or [member.topic for member in self.members])

    def _history(self) -> list[tuple[int, Message]]:
        """The consensus after each message of a member, with that message's place in the
        recording. Worked out again on every read: simple, and the recording is the one truth."""
        names = {member.topic: member.name for member in self.members}
        current: dict[str, object] = {}
        history: list[tuple[int, Message]] = []
        for index, message in enumerate(self.bus.recorder.messages()):
            if message.topic not in names or message.direction != "received":
                continue
            current[message.topic] = message.value
            if len(current) < len(names):
                continue  # not every member has spoken yet
            first = next(iter(current.values()))
            if all(value == first for value in current.values()):
                value = first
            else:
                value = Mixed(tuple((names[topic], current[topic]) for topic in names))
            history.append((index, Message(self.name, value, at=message.at)))
        return history
