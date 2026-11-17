"""What every bus can do — the one seam between BusProof and a protocol.

Everything above this seam (machines, `expect`, the evidence) talks to a `Bus` and never to an
MQTT or OPC UA library, so a new protocol changes nothing above it. A bus puts what it receives
and what it sends into its recorder; it keeps no history of its own.
"""

from typing import Protocol

from busproof.recorder import Recorder


class Bus(Protocol):
    recorder: Recorder

    async def send(self, topic: str, value: object) -> None:
        """Send `value` to `topic`, and record that it was sent."""
        ...
