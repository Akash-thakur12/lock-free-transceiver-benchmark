"""Priority Preemption & Slot Reclamation."""
from engine.buffer.slot_descriptor import BufferSlot

class PreemptionManager:
    @staticmethod
    def try_preempt_slot(slots: list, new_priority: int, current_tick: int) -> tuple[bool, int]:
        """Preempts an UNCOMMITTED lease or EXPIRED lease. NEVER preempts committed unread data."""
        # 1. First check for expired uncommitted leases
        for slot in slots:
            if slot.is_uncommitted_lease and current_tick > slot.lease_expiry_tick:
                slot.expire()
                return True, slot.slot_idx

        # 2. Check for lower-priority UNCOMMITTED leases if new_priority >= 2 (High/Critical)
        if new_priority >= 2:
            for slot in slots:
                # STRICT INVARIANT: Must be UNCOMMITTED (is_uncommitted_lease)
                if slot.is_uncommitted_lease and slot.priority < new_priority:
                    slot.expire()
                    return True, slot.slot_idx

        return False, -1
