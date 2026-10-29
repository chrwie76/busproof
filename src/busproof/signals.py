"""A signal is a handle on a value the system publishes — not the value itself.

Like a Playwright locator, a signal reads nothing when it is created. `expect(signal)` reads it,
and keeps reading until the system agrees or the time is up. A value read once and then
compared is a race against an asynchronous system.

Two kinds: a `Signal` is one value on one topic; a `Consensus` is what several signals agree on,
such as the state of a line made of machines.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from busproof.bus import Bus
from busproof.message import Message


@dataclass(frozen=True)
class Signal:
    bus: Bus
    topic: str
    # How a failure message names the signal: "capper.good_count", never the topic.
    name: str
    # Where the value sits in the payload: ("good_count",) in {"state": …, "good_count": 123}.
    # Empty when the whole payload is the value.
    path: tuple[str, ...] = ()

    def pick(self, message: Message) -> Message | None:
        """The message as this signal sees it — its value picked out of the payload — or None
        if the message does not carry this signal. What was sent never counts."""
        if message.topic != self.topic or message.direction != "received":
            return None
        value = message.value
        for key in self.path:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return replace(message, value=value)

    def latest(self) -> Message | None:
        """The newest message carrying this signal, or None."""
        mine = self.fresh(since=0)
        return mine[-1] if mine else None

    def fresh(self, since: int) -> list[Message]:
        """Messages carrying this signal after the first `since` of the recording.

        A machine that sends its whole state each time repeats `reject_count: 4` in every
        message, so every such message is fresh evidence that the value is still 4.
        """
        picked = (self.pick(message) for message in self.bus.recorder.messages(since=since))
        return [message for message in picked if message is not None]

    def silent(self) -> str:
        """Where to look when nothing arrived: the topic, since a misspelt one is likely."""
        if not self.path:
            return self.topic
        return f"{self.topic} (payload field {'.'.join(self.path)})"


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
        quiet = [member for member in self.members if member.latest() is None]
        return ", ".join(member.silent() for member in quiet or self.members)

    def _history(self) -> list[tuple[int, Message]]:
        """The consensus after each message of a member, with that message's place in the
        recording. Worked out again on every read: simple, and the recording is the one truth."""
        current: dict[int, object] = {}  # member position -> its latest value
        history: list[tuple[int, Message]] = []
        for index, message in enumerate(self.bus.recorder.messages()):
            spoke = False
            for position, member in enumerate(self.members):
                if (mine := member.pick(message)) is not None:
                    current[position] = mine.value
                    spoke = True
            if spoke and len(current) == len(self.members):  # every member has spoken
                history.append((index, Message(self.name, self._agree(current), at=message.at)))
        return history

    def _agree(self, current: dict[int, object]) -> object:
        values = [current[position] for position in range(len(self.members))]
        if all(value == values[0] for value in values):
            return values[0]
        return Mixed(tuple((member.name, current[i]) for i, member in enumerate(self.members)))
