"""Atomic Sequence Descriptors Starter Scaffold."""
from enum import Enum

class BarrierOrdering(Enum):
    ACQUIRE = 1
    RELEASE = 2
    ACQ_REL = 3
    SEQ_CST = 4

class AtomicSequence64:
    def __init__(self, initial_value: int = 0, initial_epoch: int = 0):
        self._value = initial_value
        self._epoch = initial_epoch

    @property
    def value(self) -> int:
        return self._value

    @property
    def epoch(self) -> int:
        return self._epoch

    def fetch_add(self, delta: int = 1) -> int:
        return 0

    def compare_exchange(self, expected_val: int, new_val: int, expected_epoch: int = None) -> tuple[bool, int]:
        return False, 0

class AtomicSlotDescriptor:
    def __init__(self, slot_idx: int):
        self.slot_idx = slot_idx
        self.epoch_id = 0
