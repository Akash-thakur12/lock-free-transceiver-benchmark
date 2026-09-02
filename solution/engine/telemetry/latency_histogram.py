"""Latency Percentile Calculator."""

class LatencyHistogram:
    def __init__(self):
        self.samples: list[int] = []

    def record_latency(self, ticks: int):
        self.samples.append(ticks)

    def calculate_percentiles(self) -> tuple[float, float, float]:
        if not self.samples:
            return 0.0, 0.0, 0.0
        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)
        p50_idx = int(n * 0.50)
        p99_idx = min(int(n * 0.99), n - 1)
        mean_val = sum(sorted_samples) / n
        return float(sorted_samples[p50_idx]), float(sorted_samples[p99_idx]), float(mean_val)
