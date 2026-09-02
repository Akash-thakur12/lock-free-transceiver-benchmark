"""MPMC Ring Buffer with Epoch Tokens & Strict Preemption Invariants."""
from engine.core.bit_manipulation import is_power_of_two, compute_ring_mask
from engine.buffer.slot_descriptor import BufferSlot, SlotState
from engine.buffer.linear_probing import compute_base_slot, find_candidate_slot
from engine.buffer.preemption_manager import PreemptionManager
from engine.buffer.backpressure_policy import BackpressureController
from engine.buffer.exceptions import SlotStateViolationError, BufferOverflowError

LEASE_DURATION_TICKS = 10

class MPMCRingBuffer:
    def __init__(self, capacity: int = 128, backpressure: str = "BLOCK"):
        if not is_power_of_two(capacity):
            raise ValueError(f"RingBuffer capacity {capacity} must be a strict power of 2")
        self.capacity = capacity
        self.mask = compute_ring_mask(capacity)
        self.backpressure = backpressure
        self.slots = [BufferSlot(i) for i in range(capacity)]
        self.next_lease_id = 1
        self.epoch_counter = 0
        self.active_leases: dict[int, tuple[int, int]] = {}  # lease_id -> (slot_idx, epoch)
        self.dropped_frames = 0
        self.total_committed_bytes = 0

    def acquire_lease(self, stream_id: int, seq_no: int, priority: int, current_tick: int) -> int:
        base_slot = compute_base_slot(stream_id, seq_no, self.mask)
        target_idx = find_candidate_slot(self.slots, base_slot, self.capacity, self.mask)

        # Preemption check on UNCOMMITTED leases
        if target_idx == -1:
            preempted, p_idx = PreemptionManager.try_preempt_slot(self.slots, priority, current_tick)
            if preempted:
                self.dropped_frames += 1
                target_idx = p_idx

        # Backpressure check
        if target_idx == -1:
            target_idx = BackpressureController.handle_saturation(self.backpressure, self.slots)
            if target_idx == -1:
                return -1  # Block / Yield
            self.dropped_frames += 1

        lease_id = self.next_lease_id
        self.next_lease_id += 1
        current_epoch = self.epoch_counter

        slot = self.slots[target_idx]
        slot.allocate_lease(lease_id, stream_id, seq_no, priority, current_tick + LEASE_DURATION_TICKS, current_epoch)
        self.active_leases[lease_id] = (target_idx, current_epoch)
        return lease_id

    def commit_lease(self, lease_id: int, payload: bytes) -> bool:
        if lease_id not in self.active_leases:
            raise SlotStateViolationError(f"Invalid or expired lease_id: {lease_id}")
        slot_idx, expected_epoch = self.active_leases.pop(lease_id)
        slot = self.slots[slot_idx]
        
        # Stale Authority Check: verify slot was not preempted or epoch-shifted
        if not slot.is_uncommitted_lease or slot.current_lease_id != lease_id or slot.lease_epoch != expected_epoch:
            raise SlotStateViolationError(f"Slot {slot_idx} lease expired, preempted or epoch desynchronized")

        slot.commit(payload)
        self.total_committed_bytes += len(payload)
        return True

    def drain_stream_slots(self, stream_id: int) -> list[tuple[int, bytes]]:
        ready = []
        for slot in self.slots:
            if slot.is_committed_unread and slot.stream_id == stream_id:
                data = slot.consume()
                ready.append((slot.sequence_no, data))
        return ready
