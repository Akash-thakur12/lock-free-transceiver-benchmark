"""Telemetry Metrics Snapshot Exporter."""
from engine.telemetry.latency_histogram import LatencyHistogram
from engine.telemetry.transaction_logger import TransactionLogger

class MetricsExporter:
    def __init__(self, logger: TransactionLogger, histogram: LatencyHistogram):
        self.logger = logger
        self.histogram = histogram

    def export_snapshot(self, buffer_dropped_count: int = 0) -> dict:
        p50, p99, _ = self.histogram.calculate_percentiles()
        return {
            "total_frames": self.logger.total_frames,
            "dropped_frames": self.logger.dropped_frames + buffer_dropped_count,
            "committed_bytes": self.logger.committed_bytes,
            "p50_latency_ticks": p50,
            "p99_latency_ticks": p99
        }
