"""Gapless Sliding Window Stream Reassembly."""

class StreamReassembler:
    def __init__(self):
        # stream_id -> next_expected_seq
        self.expected_seq: dict[int, int] = {}
        # stream_id -> dict[seq_no, payload]
        self.out_of_order_buffers: dict[int, dict[int, bytes]] = {}

    def ingest(self, stream_id: int, seq_no: int, payload: bytes) -> list[tuple[int, bytes]]:
        if stream_id not in self.expected_seq:
            self.expected_seq[stream_id] = seq_no
            self.out_of_order_buffers[stream_id] = {}

        next_seq = self.expected_seq[stream_id]
        ready = []

        if seq_no == next_seq:
            ready.append((seq_no, payload))
            next_seq += 1

            # Check buffered future sequences
            buf = self.out_of_order_buffers[stream_id]
            while next_seq in buf:
                ready.append((next_seq, buf.pop(next_seq)))
                next_seq += 1

            self.expected_seq[stream_id] = next_seq
        elif seq_no > next_seq:
            # Buffer out-of-order sequence
            self.out_of_order_buffers[stream_id][seq_no] = payload

        return ready
