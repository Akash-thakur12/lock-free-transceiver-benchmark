"""Crash-Recovery Checkpoint Manager & Deterministic State Serializer (Starter Scaffold)."""

class CheckpointManager:
    def __init__(self):
        pass

    def record_commit(self, stream_id: int, seq_no: int):
        pass

    def is_duplicate(self, stream_id: int, seq_no: int) -> bool:
        return False

    def serialize_state(self, transceiver_instance) -> bytes:
        return b""

    def deserialize_state(self, transceiver_instance, snapshot_bytes: bytes):
        pass
