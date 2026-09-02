"""Buffer Exceptions Starter Scaffold."""

class BufferError(Exception):
    pass

class BufferOverflowError(BufferError):
    pass

class SlotStateViolationError(BufferError):
    pass

class PreemptionConflictError(BufferError):
    pass
