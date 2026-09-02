"""Multi-Stream Collision Probing & Hash Utilities."""

def compute_base_slot(stream_id: int, seq_no: int, mask: int) -> int:
    return (stream_id * 37 + seq_no) & mask

def find_candidate_slot(slots: list, base_slot: int, capacity: int, mask: int) -> int:
    for probe in range(capacity):
        idx = (base_slot + probe) & mask
        if slots[idx].is_available:
            return idx
    return -1
