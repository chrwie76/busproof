"""A bus without a broker, for tests that must run offline.

The test plays the system: `deliver` is the system publishing a message, `sent` shows what the
code under test sent to it. Both land in the recorder, exactly as on a real bus — so whatever
works against a `FakeBus` reads the same evidence it would read from MQTT.
"""

from busproof.message import Message
from busproof.recorder import Recorder


class FakeBus:
    def __init__(self, recorder: Recorder | None = None):
        self.recorder = recorder or Recorder()

    async def send(self, topic: str, value: object) -> None:
        self.recorder.record(topic, value, direction="sent")

    def deliver(self, topic: str, value: object) -> Message:
        """Let a message arrive, as if the system had published it."""
        return self.recorder.record(topic, value)

    @property
    def sent(self) -> list[Message]:
        """Everything sent so far, oldest first."""
        return [message for message in self.recorder.messages() if message.direction == "sent"]
