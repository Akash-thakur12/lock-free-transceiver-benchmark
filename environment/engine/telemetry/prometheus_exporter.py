"""Prometheus Standard Text Metric Serializer."""

def export_prometheus_metrics(telemetry_data: dict) -> str:
    """Exports telemetry metrics in standard OpenMetrics / Prometheus scrape format."""
    lines = [
        "# HELP transceiver_total_frames Total frame count processed by transceiver",
        "# TYPE transceiver_total_frames counter",
        f"transceiver_total_frames {telemetry_data.get('total_frames', 0)}",
        "",
        "# HELP transceiver_dropped_frames Total dropped frame count under backpressure",
        "# TYPE transceiver_dropped_frames counter",
        f"transceiver_dropped_frames {telemetry_data.get('dropped_frames', 0)}",
        "",
        "# HELP transceiver_committed_bytes Total committed payload bytes",
        "# TYPE transceiver_committed_bytes counter",
        f"transceiver_committed_bytes {telemetry_data.get('committed_bytes', 0)}",
        "",
        "# HELP transceiver_p50_latency_ticks Median latency in logical ticks",
        "# TYPE transceiver_p50_latency_ticks gauge",
        f"transceiver_p50_latency_ticks {telemetry_data.get('p50_latency_ticks', 0.0):.2f}",
        "",
        "# HELP transceiver_p99_latency_ticks 99th percentile latency in logical ticks",
        "# TYPE transceiver_p99_latency_ticks gauge",
        f"transceiver_p99_latency_ticks {telemetry_data.get('p99_latency_ticks', 0.0):.2f}"
    ]
    return "\n".join(lines)
