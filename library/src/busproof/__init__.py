"""BusProof — a test language for asynchronous industrial interfaces."""

from importlib.metadata import version

from busproof.bus import Bus
from busproof.contract import ContractError, LineContract, read_line
from busproof.expect import ExpectationFailed, expect
from busproof.fake import FakeBus
from busproof.machines import Address, Line, Machine, Topics
from busproof.message import Message
from busproof.signals import Consensus, Mixed, Signal

__version__ = version("busproof")
__all__ = [
    "Address",
    "Bus",
    "Consensus",
    "ContractError",
    "ExpectationFailed",
    "FakeBus",
    "Line",
    "LineContract",
    "Machine",
    "Message",
    "Mixed",
    "Signal",
    "Topics",
    "expect",
    "read_line",
]
