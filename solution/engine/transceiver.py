"""Transceiver Main Coordinator Engine (Multi-Subsystem Architecture)."""
from engine.framing import encode_full_frame, decode_full_frame
from engine.buffer import MPMCRingBuffer
from engine.reassembly import ReassemblyEngine
from engine.scheduler import VirtualClock
from engine.scheduler.fiber_scheduler import CooperativeFiberScheduler
from engine.telemetry import TransactionLogger, LatencyHistogram, MetricsExporter
from engine.telemetry.audit_watermark import StreamWatermarkAuditor


class Transceiver:
    def __init__(self, capacity: int = 128, backpressure: str = "BLOCK"):
        self.ring_buffer = MPMCRingBuffer(capacity=capacity, backpressure=backpressure)
        self.reassembly = ReassemblyEngine()
        self.clock = VirtualClock()
        self.fibers = CooperativeFiberScheduler()
        self.watermarks = StreamWatermarkAuditor()
        self.logger = TransactionLogger()
        self.histogram = LatencyHistogram()
        self.exporter = MetricsExporter(self.logger, self.histogram)

    def encode_frame(self, stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes:
        return encode_full_frame(stream_id, seq_no, flags, payload)

    def decode_frame(self, frame_bytes: bytes) -> tuple[dict, bytes]:
        return decode_full_frame(frame_bytes)

    def publish(self, stream_id: int, seq_no: int, priority: int, payload: bytes, flags: int = 0) -> bool:
        start_tick = self.clock.current_tick
        lease_id = self.ring_buffer.acquire_lease(stream_id, seq_no, priority, start_tick)
        if lease_id == -1:
            self.logger.log_drop()
            return False

        # Encode and commit to ring buffer slot
        encoded = self.encode_frame(stream_id, seq_no, flags, payload)
        self.ring_buffer.commit_lease(lease_id, encoded)
        self.watermarks.record_commit(stream_id, seq_no)

        latency = self.clock.current_tick - start_tick + 1
        self.histogram.record_latency(latency)
        self.logger.log_commit(len(payload))
        return True

    def poll_stream(self, stream_id: int) -> list[tuple[int, bytes]]:
        raw_slots = self.ring_buffer.drain_stream_slots(stream_id)
        ready_packets = []
        for seq_no, payload_bytes in sorted(raw_slots, key=lambda x: x[0]):
            meta, payload = self.decode_frame(payload_bytes)
            emitted = self.reassembly.ingest(stream_id, meta["sequence_no"], payload)
            for s, _ in emitted:
                self.watermarks.record_drain(stream_id, s)
            ready_packets.extend(emitted)
        return ready_packets

    def schedule_fiber(self, task_id: int, priority: int, work_fn):
        self.fibers.spawn(task_id, priority, work_fn)

    def step_fibers(self) -> int:
        return self.fibers.step()

    def get_watermark_lag(self, stream_id: int) -> int:
        return self.watermarks.compute_lag(stream_id)

    def step_clock(self, ticks: int = 1):
        self.clock.tick(ticks)

    def get_telemetry(self) -> dict:
        return self.exporter.export_snapshot(self.ring_buffer.dropped_frames)
