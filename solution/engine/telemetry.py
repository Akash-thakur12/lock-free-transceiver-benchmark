"""Lock-Free Telemetry Logger & Latency Calculator."""

class TelemetryCollector:
    def __init__(self):
        self.latencies: list[int] = []
        self.total_frames = 0
        self.dropped_frames = 0
        self.committed_bytes = 0

    def record_transaction(self, latency_ticks: int, frame_bytes_len: int, status: str):
        self.total_frames += 1
        if status == "COMMITTED":
            self.latencies.append(latency_ticks)
            self.committed_bytes += frame_bytes_len
        elif status == "DROPPED":
            self.dropped_frames += 1

    def get_snapshot(self) -> dict:
        if not self.latencies:
            p50 = 0.0
            p99 = 0.0
        else:
            sorted_lat = sorted(self.latencies)
            p50_idx = int(len(sorted_lat) * 0.50)
            p99_idx = min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)
            p50 = float(sorted_lat[p50_idx])
            p99 = float(sorted_lat[p99_idx])

        return {
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "committed_bytes": self.committed_bytes,
            "p50_latency_ticks": p50,
            "p99_latency_ticks": p99
        }
