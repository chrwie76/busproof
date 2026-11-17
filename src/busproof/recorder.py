"""The recorder keeps every message of a test, in the order it arrived.

It is the memory that `expect` reads from, and the *observation* part of the evidence
(docs/CONCEPT.md §4.5): every verdict can be traced back to the messages it rests on. Nothing is
filtered or dropped while recording — a test that sees thousands of messages keeps them all.
"""

import asyncio
import time
from collections.abc import Callable

from busproof.message import Direction, Message


class Recorder:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        # The clock is a parameter so a test can control time instead of waiting for it.
        self._clock = clock
        self._start = clock()
        self._messages: list[Message] = []
        self._arrival = asyncio.Event()

    def record(self, topic: str, value: object, direction: Direction = "received") -> Message:
        """Keep a message, stamped with the seconds since the recording started."""
        message = Message(topic, value, at=self._clock() - self._start, direction=direction)
        self._messages.append(message)
        # Wake everyone waiting for this arrival, and start a fresh event for the next one.
        self._arrival.set()
        self._arrival = asyncio.Event()
        return message

    def next_arrival(self) -> asyncio.Event:
        """An event that is set when the next message is recorded.

        Take it *before* awaiting: a message recorded in between still sets the event taken,
        so a waiter cannot miss it.
        """
        return self._arrival

    def messages(self, topic: str | None = None, since: int = 0) -> list[Message]:
        """Messages so far, oldest first — only those on `topic` if one is given.

        `since` skips the first messages of the recording: `since=len(recorder)` taken at some
        moment means "only what arrived after that moment".
        """
        later = self._messages[since:]
        if topic is None:
            return later
        return [message for message in later if message.topic == topic]

    def latest(self, topic: str) -> Message | None:
        """The newest message *received* on `topic`, or None if none has arrived yet."""
        for message in reversed(self._messages):
            if message.topic == topic and message.direction == "received":
                return message
        return None

    def __len__(self) -> int:
        return len(self._messages)
