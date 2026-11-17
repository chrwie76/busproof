"""`expect` — assertions that wait, and say what they saw.

An asynchronous system answers a command now and shows its effect later. So every matcher keeps
reading until the system agrees or the time is up; a test never sleeps first. When it fails, the
message lists what the signal showed in the meantime, so a red run explains itself:

    expected capper.state to be 'Execute' within 10s — seen: 'Idle' → 'Starting' (2 messages)

How the matchers are named — the name tells what kind of check it is:

- `to_be…` asks *where the signal ends up*: `to_be("Execute")`.
- A verb asks *what the signal does over time*: `rises_by(5)`, `remains(...)`.
- `within=` is for what must happen at some point; `during=` for what must hold all along.
  Both are in seconds, like every time in Python.

Each matcher opens a *window* when it is called: what the signal showed at that moment, and every
message after it. Nothing from before the window counts as evidence that something happens now.
"""

import asyncio
from collections.abc import Callable
from typing import NoReturn, TypeGuard

from busproof.message import Message, show
from busproof.signals import Consensus, Signal

# Seconds to wait when a test does not say. busproof.toml will be able to change it.
DEFAULT_WITHIN = 5.0


class ExpectationFailed(AssertionError):
    """An expectation the system did not meet. An AssertionError, so pytest reports a failure."""


def expect(signal: Signal | Consensus) -> "Expectation":
    return Expectation(signal)


class Expectation:
    def __init__(self, signal: Signal | Consensus):
        self.signal = signal
        self.recorder = signal.bus.recorder
        self._window_start = 0
        self._before: Message | None = None

    async def to_be(self, expected: object, *, within: float = DEFAULT_WITHIN) -> None:
        """Pass as soon as the signal's latest value is `expected`."""
        self._open_window()
        if await self._wait_until(lambda: self._latest_is(expected), within):
            return
        self._fail(f"to be {show(expected)} within {within:g}s", self._seen(within))

    async def rises_by(self, amount: float, *, within: float = DEFAULT_WITHIN) -> None:
        """Pass as soon as the signal has risen by at least `amount` since the window opened.

        The baseline is the value when the expectation starts — not one read earlier in the
        test: a counter that moved during setup is no evidence that it moves now.
        """
        self._open_window()
        if await self._wait_until(lambda: self._rise() >= amount, within):
            return
        what = f"to rise by {amount:g} within {within:g}s"
        values = self._values()
        not_numbers = [value for value in values if not is_number(value)]
        if not_numbers:
            self._fail(what, f"{show(not_numbers[0])} is not a number")
        rose = f"it rose by {self._rise():g}; " if values else ""
        self._fail(what, rose + self._seen(within))

    async def remains(self, *, during: float) -> None:
        """Pass if the signal keeps its value for `during` seconds, confirmed by fresh messages.

        Silence is not stability: a signal that sends nothing in the window fails — otherwise a
        misspelt name would be the easiest green there is. A change fails at once.
        """
        self._open_window()
        changed = await self._wait_until(self._changed, during)
        values = self._values()
        value = f" {show(values[0])}" if values else ""
        what = f"to remain{value} for {during:g}s"
        if changed:
            self._fail(what, "it changed; " + self._seen(during))
        if not self._fresh():
            self._fail(
                what,
                "no message arrived in the window, so 'unchanged' cannot be told from 'silent'; "
                + self._seen(during),
            )

    # --- the window ------------------------------------------------------------------------

    def _open_window(self) -> None:
        self._window_start = len(self.recorder)
        self._before = self.signal.latest()

    def _fresh(self) -> list[Message]:
        """Messages received for the signal since the window opened."""
        return self.signal.fresh(self._window_start)

    def _values(self) -> list[object]:
        """The value at the start of the window (if any), then every value received in it."""
        start = [self._before.value] if self._before else []
        return start + [message.value for message in self._fresh()]

    def _latest_is(self, expected: object) -> bool:
        values = self._values()
        return bool(values) and values[-1] == expected

    def _rise(self) -> float:
        """How far the signal rose since the window opened; 0 until it has numbers to compare."""
        values = self._values()
        numbers = [value for value in values if is_number(value)]
        if not numbers or len(numbers) != len(values):
            return 0
        return numbers[-1] - numbers[0]

    def _changed(self) -> bool:
        values = self._values()
        return any(value != values[0] for value in values[1:])

    async def _wait_until(self, condition: Callable[[], bool], seconds: float) -> bool:
        """Read every arrival until `condition` holds (True) or `seconds` have passed (False)."""
        deadline = asyncio.get_running_loop().time() + seconds
        while True:
            if condition():
                return True
            # Taken before awaiting, so a message recorded in between is not missed.
            arrival = self.recorder.next_arrival()
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return False
            try:
                async with asyncio.timeout(remaining):
                    await arrival.wait()
            except TimeoutError:
                pass  # the loop checks once more, then gives up

    def _seen(self, window: float) -> str:
        return describe(self._before, self._fresh(), window, self.signal.silent())

    def _fail(self, what: str, detail: str) -> NoReturn:
        raise ExpectationFailed(f"expected {self.signal.name} {what} — {detail}")


def is_number(value: object) -> TypeGuard[int | float]:
    # bool is an int in Python, but True is not a count.
    return isinstance(value, int | float) and not isinstance(value, bool)


def describe(before: Message | None, seen: list[Message], window: float, topic: str) -> str:
    """What a signal showed: its value at the start, then each change, repeats collapsed."""
    if before is None and not seen:
        # Name the topic: when nothing ever arrives, a misspelt address is the first suspect.
        return f"nothing arrived on {topic}"
    values = ([before.value] if before else []) + [message.value for message in seen]
    changes = [value for i, value in enumerate(values) if i == 0 or value != values[i - 1]]
    chain = " → ".join(show(value) for value in changes)
    if not seen:
        return f"seen: {chain} (no new message in {window:g}s)"
    count = f"{len(seen)} message" + ("" if len(seen) == 1 else "s")
    return f"seen: {chain} ({count})"
