"""Stream Watermark & High-Watermark Lag Auditor."""

class StreamWatermarkAuditor:
    def __init__(self):
        self.high_watermarks: dict[int, int] = {}  # stream_id -> max committed sequence
        self.low_watermarks: dict[int, int] = {}   # stream_id -> min unconsumed sequence
        self.total_watermark_updates = 0

    def record_commit(self, stream_id: int, seq_no: int):
        current_hw = self.high_watermarks.get(stream_id, -1)
        if seq_no > current_hw:
            self.high_watermarks[stream_id] = seq_no
        if stream_id not in self.low_watermarks:
            self.low_watermarks[stream_id] = seq_no
        self.total_watermark_updates += 1

    def record_drain(self, stream_id: int, drained_seq: int):
        self.low_watermarks[stream_id] = drained_seq + 1

    def compute_lag(self, stream_id: int) -> int:
        hw = self.high_watermarks.get(stream_id, 0)
        lw = self.low_watermarks.get(stream_id, 0)
        return max(0, hw - lw)
