"""Runtime Configuration Schema & Validation Parser."""
from typing import NamedTuple

class TransceiverConfig(NamedTuple):
    ring_buffer_capacity: int = 128
    backpressure_mode: str = "BLOCK"
    max_payload_size: int = 4096
    lease_duration_ticks: int = 10
    enable_telemetry: bool = True
    sliding_window_depth: int = 1024

def validate_config(cfg: TransceiverConfig) -> bool:
    if cfg.ring_buffer_capacity <= 0 or (cfg.ring_buffer_capacity & (cfg.ring_buffer_capacity - 1)) != 0:
        raise ValueError(f"Invalid capacity {cfg.ring_buffer_capacity}: must be a power of 2")
    if cfg.backpressure_mode not in ("BLOCK", "DROP_OLDEST", "REJECT"):
        raise ValueError(f"Invalid backpressure mode: {cfg.backpressure_mode}")
    if cfg.max_payload_size > 65535:
        raise ValueError(f"Max payload size {cfg.max_payload_size} exceeds 16-bit field limit")
    return True
