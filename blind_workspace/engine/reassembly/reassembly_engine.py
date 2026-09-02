"""Multi-Stream Reassembly Engine."""
from engine.reassembly.sliding_window import GaplessSlidingWindow

class ReassemblyEngine:
    def __init__(self):
        self.windows: dict[int, GaplessSlidingWindow] = {}

    def get_or_create_window(self, stream_id: int) -> GaplessSlidingWindow:
        if stream_id not in self.windows:
            self.windows[stream_id] = GaplessSlidingWindow(stream_id)
        return self.windows[stream_id]

    def ingest(self, stream_id: int, seq_no: int, payload: bytes) -> list[tuple[int, bytes]]:
        window = self.get_or_create_window(stream_id)
        return window.ingest_packet(seq_no, payload)

    def get_expected_seq(self, stream_id: int) -> int:
        if stream_id in self.windows:
            return self.windows[stream_id].tracker.expected_seq
        return 0
