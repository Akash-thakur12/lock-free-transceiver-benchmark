"""Memory Fence Coordinator Starter Scaffold."""

class MemoryFenceViolationError(Exception):
    pass

class EpochDesyncError(Exception):
    pass

class MemoryFenceCoordinator:
    def __init__(self):
        self._global_fence_epoch = 0

    @property
    def global_epoch(self) -> int:
        return self._global_fence_epoch

    def advance_epoch(self) -> int:
        return 0

    def acquire_slot_fence(self, slot, current_epoch: int):
        pass

    def release_slot_fence(self, slot, current_epoch: int):
        pass
