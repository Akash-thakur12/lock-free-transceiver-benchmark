"""Atomic Sequence Descriptors, Epoch Markers & CAS Simulation."""
from enum import Enum
from engine.core.bit_manipulation import wrap_uint64, wrap_uint32

class BarrierOrdering(Enum):
    ACQUIRE = 1
    RELEASE = 2
    ACQ_REL = 3
    SEQ_CST = 4

class AtomicSequence64:
    def __init__(self, initial_value: int = 0, initial_epoch: int = 0):
        self._value = wrap_uint64(initial_value)
        self._epoch = wrap_uint32(initial_epoch)
        self._aba_counter = 0

    @property
    def value(self) -> int:
        return self._value

    @property
    def epoch(self) -> int:
        return self._epoch

    def fetch_add(self, delta: int = 1) -> int:
        old_val = self._value
        new_val = wrap_uint64(old_val + delta)
        # Check wraparound to increment epoch
        if new_val < old_val:
            self._epoch = wrap_uint32(self._epoch + 1)
        self._value = new_val
        self._aba_counter += 1
        return old_val

    def compare_exchange(self, expected_val: int, new_val: int, expected_epoch: int = None) -> tuple[bool, int]:
        if self._value != expected_val:
            return False, self._value
        if expected_epoch is not None and self._epoch != expected_epoch:
            return False, self._value

        new_v = wrap_uint64(new_val)
        if new_v < self._value:
            self._epoch = wrap_uint32(self._epoch + 1)
        self._value = new_v
        self._aba_counter += 1
        return True, expected_val


class AtomicSlotDescriptor:
    def __init__(self, slot_idx: int):
        self.slot_idx = slot_idx
        self.epoch_id = 0
        self.stream_id = 0
        self.sequence_no = 0
        self.producer_turn = 0
        self.consumer_turn = 0
        self.priority_tier = 0  # 0=Normal, 1=Medium, 2=High, 3=Critical
        self.lease_expiry_tick = 0
        self.is_leased = False
        self.is_committed = False
        self.is_consumed = True
        self.payload: bytes = b""

    def reset(self, new_epoch: int):
        self.epoch_id = new_epoch
        self.stream_id = 0
        self.sequence_no = 0
        self.producer_turn = 0
        self.consumer_turn = 0
        self.priority_tier = 0
        self.lease_expiry_tick = 0
        self.is_leased = False
        self.is_committed = False
        self.is_consumed = True
        self.payload = b""
