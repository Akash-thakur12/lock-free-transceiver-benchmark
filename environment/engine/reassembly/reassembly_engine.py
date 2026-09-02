"""Reassembly Engine Starter Scaffold."""

class ReassemblyEngine:
    def __init__(self):
        pass

    def ingest(self, stream_id: int, seq_no: int, payload: bytes) -> list[tuple[int, bytes]]:
        return []

    def get_expected_seq(self, stream_id: int) -> int:
        return 0
