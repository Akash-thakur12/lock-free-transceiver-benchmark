"""Core Atomics Starter Scaffold."""
from .bit_manipulation import is_power_of_two, align_to_cache_line, compute_ring_mask, wrap_uint64, wrap_uint32
from .atomic_types import BarrierOrdering, AtomicSequence64, AtomicSlotDescriptor
from .memory_fence import MemoryFenceCoordinator, MemoryFenceViolationError, EpochDesyncError

__all__ = [
    "is_power_of_two", "align_to_cache_line", "compute_ring_mask", "wrap_uint64", "wrap_uint32",
    "BarrierOrdering", "AtomicSequence64", "AtomicSlotDescriptor",
    "MemoryFenceCoordinator", "MemoryFenceViolationError", "EpochDesyncError"
]
