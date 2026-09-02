"""Stream Watermark & High-Watermark Lag Auditor (Starter Scaffold)."""

class StreamWatermarkAuditor:
    def __init__(self):
        pass

    def record_commit(self, stream_id: int, seq_no: int):
        pass

    def record_drain(self, stream_id: int, drained_seq: int):
        pass

    def compute_lag(self, stream_id: int) -> int:
        return 0
