"""Bitwise Manipulation & Cache-Line Alignment Utilities."""

UINT64_MAX = (1 << 64) - 1
UINT32_MAX = (1 << 32) - 1
CACHE_LINE_BYTES = 64

def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0

def align_to_cache_line(offset: int) -> int:
    return (offset + CACHE_LINE_BYTES - 1) & ~(CACHE_LINE_BYTES - 1)

def compute_ring_mask(capacity: int) -> int:
    if not is_power_of_two(capacity):
        raise ValueError(f"Capacity {capacity} must be a strict power of 2")
    return capacity - 1

def wrap_uint64(val: int) -> int:
    return val & UINT64_MAX

def wrap_uint32(val: int) -> int:
    return val & UINT32_MAX
