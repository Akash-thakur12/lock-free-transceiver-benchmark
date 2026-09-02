"""Buffer Exception Hierarchy."""

class BufferError(Exception):
    """Base exception for ring buffer operations."""
    pass

class BufferOverflowError(BufferError):
    """Raised when buffer is saturated under REJECT backpressure policy."""
    pass

class SlotStateViolationError(BufferError):
    """Raised when accessing or committing an unleased, expired, or invalid slot."""
    pass

class PreemptionConflictError(BufferError):
    """Raised when preemption contract is violated."""
    pass
