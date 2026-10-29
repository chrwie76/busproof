"""BusProof — a test language for asynchronous industrial interfaces."""

from importlib.metadata import version

from busproof.expect import ExpectationFailed, expect
from busproof.signals import Signal

__version__ = version("busproof")
__all__ = ["ExpectationFailed", "Signal", "expect"]
