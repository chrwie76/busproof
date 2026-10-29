"""The recorder keeps every message of a test, in the order it arrived.

It is the memory that `expect` reads from, and the *observation* part of the evidence
(docs/CONCEPT.md §4.5): every verdict can be traced back to the messages it rests on. Nothing is
filtered or dropped while recording — a test that sees thousands of messages keeps them all.
"""

import time
from collections.abc import Callable

from busproof.message import Direction, Message


class Recorder:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        # The clock is a parameter so a test can control time instead of waiting for it.
        self._clock = clock
        self._start = clock()
        self._messages: list[Message] = []

    def record(self, topic: str, value: object, direction: Direction = "received") -> Message:
        """Keep a message, stamped with the seconds since the recording started."""
        message = Message(topic, value, at=self._clock() - self._start, direction=direction)
        self._messages.append(message)
        return message

    def messages(self, topic: str | None = None) -> list[Message]:
        """All messages so far, oldest first — only those on `topic` if one is given."""
        if topic is None:
            return list(self._messages)
        return [message for message in self._messages if message.topic == topic]

    def latest(self, topic: str) -> Message | None:
        """The newest message *received* on `topic`, or None if none has arrived yet."""
        for message in reversed(self._messages):
            if message.topic == topic and message.direction == "received":
                return message
        return None

    def __len__(self) -> int:
        return len(self._messages)
