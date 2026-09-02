"""Buffer Package."""
from .exceptions import (
    BufferError, BufferOverflowError, SlotStateViolationError, PreemptionConflictError
)
from .slot_descriptor import BufferSlot, SlotState
from .linear_probing import compute_base_slot, find_candidate_slot
from .preemption_manager import PreemptionManager
from .backpressure_policy import BackpressurePolicy, BackpressureController
from .mpmc_ring_buffer import MPMCRingBuffer

__all__ = [
    "BufferError", "BufferOverflowError", "SlotStateViolationError", "PreemptionConflictError",
    "BufferSlot", "SlotState", "compute_base_slot", "find_candidate_slot",
    "PreemptionManager", "BackpressurePolicy", "BackpressureController",
    "MPMCRingBuffer"
]
