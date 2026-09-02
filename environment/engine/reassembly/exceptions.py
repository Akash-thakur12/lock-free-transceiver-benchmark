"""Reassembly Exceptions Starter Scaffold."""

class ReassemblyError(Exception):
    pass

class SequenceBreakError(ReassemblyError):
    pass

class DuplicateSequenceError(ReassemblyError):
    pass

class WindowCapacityOverflowError(ReassemblyError):
    pass
