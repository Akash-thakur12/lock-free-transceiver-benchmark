"""Gapless Sliding Window Reassembly with Modular uint64 Wraparound Arithmetic."""
from engine.reassembly.stream_tracker import StreamTracker
from engine.reassembly.out_of_order_queue import OutOfOrderQueue

UINT64_MASK = (1 << 64) - 1
HALF_UINT64 = (1 << 63)

def uint64_distance(seq: int, expected: int) -> int:
    """Computes directional distance between two uint64 sequence numbers across wraparound."""
    return (seq - expected) & UINT64_MASK

class GaplessSlidingWindow:
    def __init__(self, stream_id: int):
        self.stream_id = stream_id
        self.tracker = StreamTracker(stream_id)
        self.queue = OutOfOrderQueue()

    def ingest_packet(self, seq_no: int, payload: bytes) -> list[tuple[int, bytes]]:
        self.tracker.initialize_if_new(seq_no)
        expected = self.tracker.expected_seq
        ready_packets = []

        dist = uint64_distance(seq_no, expected)

        if dist == 0:
            # Exact in-order sequence match
            ready_packets.append((seq_no, payload))
            expected = (expected + 1) & UINT64_MASK

            # Drain contiguous future sequences staged in out-of-order queue
            while self.queue.has_seq(expected):
                next_payload = self.queue.pop_seq(expected)
                ready_packets.append((expected, next_payload))
                expected = (expected + 1) & UINT64_MASK

            self.tracker.expected_seq = expected
        elif 0 < dist < HALF_UINT64:
            # Future sequence -> stage in out-of-order buffer
            self.queue.buffer_packet(seq_no, payload)
        else:
            # Past / Stale / Duplicate sequence (dist >= HALF_UINT64) -> drop
            pass

        return ready_packets
