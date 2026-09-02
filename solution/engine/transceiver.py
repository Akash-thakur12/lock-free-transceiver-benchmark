"""Transceiver Main Coordinator Engine."""
from engine.codec import encode_frame, decode_frame, TransceiverError
from engine.ring_buffer import RingBuffer
from engine.reassembly import StreamReassembler
from engine.scheduler import VirtualClock
from engine.telemetry import TelemetryCollector


class Transceiver:
    def __init__(self, capacity: int = 128, backpressure: str = "BLOCK"):
        self.ring_buffer = RingBuffer(capacity=capacity, backpressure=backpressure)
        self.reassembler = StreamReassembler()
        self.clock = VirtualClock()
        self.telemetry = TelemetryCollector()
        self.pending_transmissions: dict[int, tuple[int, int, bytes, int]] = {}  # lease_id -> (stream_id, seq_no, payload, start_tick)

    def encode_frame(self, stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes:
        return encode_frame(stream_id, seq_no, flags, payload)

    def decode_frame(self, frame_bytes: bytes) -> tuple[dict, bytes]:
        return decode_frame(frame_bytes)

    def publish(self, stream_id: int, seq_no: int, priority: int, payload: bytes, flags: int = 0) -> bool:
        start_tick = self.clock.current_tick
        lease_id = self.ring_buffer.acquire_lease(stream_id, seq_no, priority, start_tick)
        if lease_id == -1:
            self.telemetry.record_transaction(0, len(payload), "DROPPED")
            return False

        # Encode and commit
        encoded = self.encode_frame(stream_id, seq_no, flags, payload)
        self.ring_buffer.commit_lease(lease_id, encoded)

        # Ingest into stream reassembly
        self.reassembler.ingest(stream_id, seq_no, payload)
        
        latency = self.clock.current_tick - start_tick + 1
        self.telemetry.record_transaction(latency, len(payload), "COMMITTED")
        return True

    def poll_stream(self, stream_id: int) -> list[tuple[int, bytes]]:
        # Drain ready in-order frames
        slot_idx = 0
        ready = []
        for slot in self.ring_buffer.slots:
            if slot.is_committed and not slot.is_consumed and slot.stream_id == stream_id:
                meta, payload = self.decode_frame(slot.payload)
                ready.append((meta["sequence_no"], payload))
                slot.is_consumed = True
        return sorted(ready, key=lambda x: x[0])

    def step_clock(self, ticks: int = 1):
        self.clock.tick(ticks)

    def get_telemetry(self) -> dict:
        snap = self.telemetry.get_snapshot()
        snap["dropped_frames"] += self.ring_buffer.dropped_frames
        return snap
