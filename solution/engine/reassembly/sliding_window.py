"""Gapless Sliding Window Reassembly Coordinator."""
from engine.reassembly.stream_tracker import StreamTracker
from engine.reassembly.out_of_order_queue import OutOfOrderQueue
from engine.reassembly.exceptions import DuplicateSequenceError

class GaplessSlidingWindow:
    def __init__(self, stream_id: int):
        self.stream_id = stream_id
        self.tracker = StreamTracker(stream_id)
        self.queue = OutOfOrderQueue()

    def ingest_packet(self, seq_no: int, payload: bytes) -> list[tuple[int, bytes]]:
        self.tracker.initialize_if_new(seq_no)
        expected = self.tracker.expected_seq
        ready_packets = []

        if seq_no == expected:
            ready_packets.append((seq_no, payload))
            expected += 1

            # Drain contiguous ready packets from out-of-order queue
            while self.queue.has_seq(expected):
                next_payload = self.queue.pop_seq(expected)
                ready_packets.append((expected, next_payload))
                expected += 1

            self.tracker.expected_seq = expected
        elif seq_no > expected:
            # Future sequence -> stage in out-of-order buffer
            self.queue.buffer_packet(seq_no, payload)
        else:
            # Duplicate / Stale sequence (seq_no < expected) -> silently drop or ignore
            pass

        return ready_packets
