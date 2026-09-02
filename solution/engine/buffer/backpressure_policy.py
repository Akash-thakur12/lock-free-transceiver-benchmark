"""Backpressure Controllers: BLOCK, DROP_OLDEST, REJECT."""
from enum import Enum
from engine.buffer.exceptions import BufferOverflowError

class BackpressurePolicy(Enum):
    BLOCK = "BLOCK"
    DROP_OLDEST = "DROP_OLDEST"
    REJECT = "REJECT"

class BackpressureController:
    @staticmethod
    def handle_saturation(policy: str, slots: list) -> int:
        if policy == BackpressurePolicy.REJECT.value:
            return -1  # Reject immediately without waiting or evicting
        elif policy == BackpressurePolicy.DROP_OLDEST.value:
            # Genuine DROP_OLDEST: find the unconsumed committed slot with lowest sequence_no / turn
            oldest_idx = -1
            lowest_seq = float("inf")
            for slot in slots:
                if slot.is_committed_unread and slot.sequence_no < lowest_seq:
                    lowest_seq = slot.sequence_no
                    oldest_idx = slot.slot_idx

            if oldest_idx != -1:
                slots[oldest_idx].consume()  # Drop oldest unconsumed committed slot
                return oldest_idx
            else:
                # If no committed slot, return slot 0
                return 0
        else:
            # BLOCK / Yield
            return -1
