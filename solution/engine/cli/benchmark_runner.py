"""CLI Diagnostic Throughput & Latency Benchmark Harness."""
import time

def run_throughput_benchmark(transceiver_instance, iterations: int = 1000) -> dict:
    """Measures synthetic sustained stream publication throughput."""
    payload = b"BENCHMARK_STREAM_DATA_PAYLOAD_BLOCK_128"
    start_time = time.perf_counter()

    success_count = 0
    for seq in range(iterations):
        ok = transceiver_instance.publish(stream_id=1, seq_no=seq, priority=0, payload=payload)
        if ok:
            success_count += 1

    elapsed = time.perf_counter() - start_time
    throughput_ops = success_count / elapsed if elapsed > 0 else 0.0

    return {
        "iterations": iterations,
        "success_count": success_count,
        "elapsed_seconds": round(elapsed, 4),
        "ops_per_second": round(throughput_ops, 2),
        "telemetry": transceiver_instance.get_telemetry()
    }
