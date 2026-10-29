"""`expect` — assertions that wait, and say what they saw.

An asynchronous system answers a command now and shows its effect later. So every matcher keeps
reading until the system agrees or a deadline says it will not; a test never sleeps first.
When it fails, the message lists what the signal showed in the meantime, so a red run explains
itself without opening a log:

    expected capper.state to equal 'Execute' within 10s — seen: 'Idle' → 'Starting' (2 messages)
"""

import asyncio

from busproof.message import Message
from busproof.signals import Signal

# Used when a test does not say how long to wait. busproof.toml will be able to change it.
DEFAULT_WITHIN_S = 5.0


class ExpectationFailed(AssertionError):
    """An expectation the system did not meet. An AssertionError, so pytest reports a failure."""


def expect(signal: Signal) -> "Expectation":
    return Expectation(signal)


class Expectation:
    def __init__(self, signal: Signal):
        self.signal = signal
        self.recorder = signal.bus.recorder

    async def to_equal(self, expected: object, *, within_s: float = DEFAULT_WITHIN_S) -> None:
        """Pass as soon as the signal's latest value equals `expected`."""
        window_start = len(self.recorder)
        before = self.recorder.latest(self.signal.topic)
        deadline = asyncio.get_running_loop().time() + within_s

        while True:
            latest = self.recorder.latest(self.signal.topic)
            if latest is not None and latest.value == expected:
                return

            arrival = self.recorder.next_arrival()
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                seen = self._received(since=window_start)
                raise ExpectationFailed(
                    f"expected {self.signal.name} to equal {expected!r} within {within_s:g}s"
                    f" — {describe(before, seen, within_s, self.signal.topic)}"
                )
            try:
                async with asyncio.timeout(remaining):
                    await arrival.wait()
            except TimeoutError:
                pass  # the loop checks once more, then reports

    def _received(self, since: int) -> list[Message]:
        messages = self.recorder.messages(self.signal.topic, since=since)
        return [message for message in messages if message.direction == "received"]


def describe(before: Message | None, seen: list[Message], within_s: float, topic: str) -> str:
    """What a signal showed: its value at the start, then each change, repeats collapsed."""
    if before is None and not seen:
        # Name the topic: when nothing ever arrives, a misspelt address is the first suspect.
        return f"nothing arrived on {topic}"
    values = ([before.value] if before else []) + [message.value for message in seen]
    changes = [value for i, value in enumerate(values) if i == 0 or value != values[i - 1]]
    chain = " → ".join(repr(value) for value in changes)
    if not seen:
        return f"seen: {chain} (no new message in {within_s:g}s)"
    count = f"{len(seen)} message" + ("" if len(seen) == 1 else "s")
    return f"seen: {chain} ({count})"
