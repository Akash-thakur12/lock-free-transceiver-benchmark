"""Memory Fence Barrier & Epoch Ordering Coordinator."""
from engine.core.atomic_types import BarrierOrdering, AtomicSlotDescriptor

class MemoryFenceViolationError(Exception):
    pass

class EpochDesyncError(Exception):
    pass

class MemoryFenceCoordinator:
    def __init__(self):
        self._global_fence_epoch = 0
        self._pending_acquires: set[int] = set()

    @property
    def global_epoch(self) -> int:
        return self._global_fence_epoch

    def advance_epoch(self) -> int:
        self._global_fence_epoch += 1
        return self._global_fence_epoch

    def acquire_slot_fence(self, slot: AtomicSlotDescriptor, current_epoch: int):
        if slot.epoch_id > current_epoch:
            raise EpochDesyncError(f"Slot epoch {slot.epoch_id} exceeds current global epoch {current_epoch}")
        self._pending_acquires.add(slot.slot_idx)

    def release_slot_fence(self, slot: AtomicSlotDescriptor, current_epoch: int):
        if slot.slot_idx in self._pending_acquires:
            self._pending_acquires.remove(slot.slot_idx)
        slot.epoch_id = current_epoch
