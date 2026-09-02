"""Reassembly Exception Hierarchy."""

class ReassemblyError(Exception):
    """Base exception for packet reassembly errors."""
    pass

class SequenceBreakError(ReassemblyError):
    """Raised when an unrecoverable sequence break occurs."""
    pass

class DuplicateSequenceError(ReassemblyError):
    """Raised when an already processed duplicate sequence number is received."""
    pass

class WindowCapacityOverflowError(ReassemblyError):
    """Raised when out-of-order buffer exceeds window capacity."""
    pass
