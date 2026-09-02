"""Slot Descriptors & Epoch Token Authority."""
from enum import Enum

class SlotState(Enum):
    IDLE = 0
    LEASED = 1
    COMMITTED = 2
    CONSUMED = 3
    EXPIRED = 4

class BufferSlot:
    def __init__(self, slot_idx: int):
        self.slot_idx = slot_idx
        self.current_lease_id = 0
        self.lease_epoch = 0
        self.stream_id = 0
        self.sequence_no = 0
        self.priority = 0
        self.lease_expiry_tick = 0
        self.state = SlotState.IDLE
        self.payload: bytes = b""

    @property
    def is_available(self) -> bool:
        return self.state in (SlotState.IDLE, SlotState.CONSUMED, SlotState.EXPIRED)

    @property
    def is_uncommitted_lease(self) -> bool:
        return self.state == SlotState.LEASED

    @property
    def is_committed_unread(self) -> bool:
        return self.state == SlotState.COMMITTED

    def allocate_lease(self, lease_id: int, stream_id: int, seq_no: int, priority: int, expiry_tick: int, epoch: int):
        self.current_lease_id = lease_id
        self.lease_epoch = epoch
        self.stream_id = stream_id
        self.sequence_no = seq_no
        self.priority = priority
        self.lease_expiry_tick = expiry_tick
        self.state = SlotState.LEASED
        self.payload = b""

    def commit(self, payload: bytes):
        self.payload = payload
        self.state = SlotState.COMMITTED

    def consume(self) -> bytes:
        data = self.payload
        self.state = SlotState.CONSUMED
        return data

    def expire(self):
        self.state = SlotState.EXPIRED
        self.current_lease_id = 0
        self.payload = b""
