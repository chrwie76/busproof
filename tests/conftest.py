"""Fixtures shared by the tests of BusProof itself.

Tests here check the tool, never a plant: tests/unit has one file per module of the library
(test_expect.py checks expect.py), tests/repo checks the repository around it. Tests *of a plant*
written *with* BusProof live in demo/line-tests.
"""

import asyncio
from collections.abc import Callable

import pytest

from busproof.fake import FakeBus


class Clock:
    """A clock the test moves by hand, so no test has to wait for real time to pass."""

    def __init__(self, now: float = 100.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def bus() -> FakeBus:
    return FakeBus()


@pytest.fixture
def deliver_later(bus: FakeBus) -> Callable[[float, str, object], None]:
    """Let the system publish a value a little later, while the test is already waiting."""

    def deliver(seconds: float, topic: str, value: object) -> None:
        asyncio.get_running_loop().call_later(seconds, bus.deliver, topic, value)

    return deliver
