"""BusProof — a test language for asynchronous industrial interfaces."""

from importlib.metadata import version

from busproof.expect import ExpectationFailed, expect
from busproof.machines import Line, Machine, Topics
from busproof.signals import Consensus, Mixed, Signal

__version__ = version("busproof")
__all__ = [
    "Consensus",
    "ExpectationFailed",
    "Line",
    "Machine",
    "Mixed",
    "Signal",
    "Topics",
    "expect",
]
