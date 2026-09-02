"""Power-of-Two Lock-Free MPMC Ring Buffer."""
from engine.codec import BufferOverflowError, SlotStateViolationError

class Slot:
    def __init__(self):
        self.sequence_no = 0
        self.stream_id = 0
        self.priority = 0
        self.lease_expiry_tick = 0
        self.is_leased = False
        self.is_committed = False
        self.is_consumed = True
        self.payload: bytes = b""


class RingBuffer:
    def __init__(self, capacity: int = 128, backpressure: str = "BLOCK"):
        if capacity <= 0 or (capacity & (capacity - 1)) != 0:
            raise ValueError(f"Capacity {capacity} must be a positive power of 2")
        self.capacity = capacity
        self.mask = capacity - 1
        self.backpressure = backpressure
        self.slots = [Slot() for _ in range(capacity)]
        self.next_lease_id = 1
        self.active_leases: dict[int, int] = {}  # lease_id -> slot_idx
        self.dropped_frames = 0
        self.total_committed_bytes = 0

    def acquire_lease(self, stream_id: int, seq_no: int, priority: int, current_tick: int) -> int:
        base_slot = (stream_id * 37 + seq_no) & self.mask
        target_slot_idx = -1

        # Probe for available slot
        for probe in range(self.capacity):
            idx = (base_slot + probe) & self.mask
            slot = self.slots[idx]

            if not slot.is_leased or slot.is_consumed:
                target_slot_idx = idx
                break
            elif priority >= 2 and slot.priority < priority:
                slot.is_leased = False
                slot.is_committed = False
                self.dropped_frames += 1
                target_slot_idx = idx
                break
            elif current_tick > slot.lease_expiry_tick and not slot.is_committed:
                slot.is_leased = False
                self.dropped_frames += 1
                target_slot_idx = idx
                break

        if target_slot_idx == -1:
            if self.backpressure == "REJECT":
                raise BufferOverflowError("Ring buffer is fully occupied")
            elif self.backpressure == "DROP_OLDEST":
                target_slot_idx = base_slot
                self.slots[target_slot_idx].is_consumed = True
                self.dropped_frames += 1
            else:
                return -1  # Yield / Block

        slot = self.slots[target_slot_idx]
        slot.sequence_no = seq_no
        slot.stream_id = stream_id
        slot.priority = priority
        slot.lease_expiry_tick = current_tick + 10
        slot.is_leased = True
        slot.is_committed = False
        slot.is_consumed = False
        slot.payload = b""

        lease_id = self.next_lease_id
        self.next_lease_id += 1
        self.active_leases[lease_id] = target_slot_idx
        return lease_id

    def commit_lease(self, lease_id: int, payload: bytes) -> bool:
        if lease_id not in self.active_leases:
            raise SlotStateViolationError(f"Invalid or expired lease_id {lease_id}")
        slot_idx = self.active_leases.pop(lease_id)
        slot = self.slots[slot_idx]
        if not slot.is_leased:
            raise SlotStateViolationError(f"Slot {slot_idx} was preempted before commit")

        slot.payload = payload
        slot.is_committed = True
        self.total_committed_bytes += len(payload)
        return True
