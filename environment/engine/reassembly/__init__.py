"""Reassembly Package Starter Scaffold."""
from .exceptions import (
    ReassemblyError, SequenceBreakError, DuplicateSequenceError, WindowCapacityOverflowError
)
from .reassembly_engine import ReassemblyEngine

StreamReassembler = ReassemblyEngine

__all__ = [
    "ReassemblyError", "SequenceBreakError", "DuplicateSequenceError", "WindowCapacityOverflowError",
    "ReassemblyEngine", "StreamReassembler"
]
