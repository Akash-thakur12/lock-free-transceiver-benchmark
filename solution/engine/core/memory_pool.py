"""Zero-Copy Memory Pool & Cache-Aligned Slab Arena Manager."""
from typing import Optional

class MemoryPoolChunk:
    """Represents a contiguous cache-aligned memory slab chunk."""
    def __init__(self, chunk_id: int, size_bytes: int, stride_alignment: int = 64):
        self.chunk_id = chunk_id
        self.size_bytes = size_bytes
        self.stride_alignment = stride_alignment
        self.raw_buffer = bytearray(size_bytes)
        self.is_allocated = False
        self.allocated_length = 0
        self.reference_count = 0

    def acquire(self, requested_length: int) -> memoryview:
        if requested_length > self.size_bytes:
            raise ValueError(f"Requested length {requested_length} exceeds chunk capacity {self.size_bytes}")
        self.is_allocated = True
        self.allocated_length = requested_length
        self.reference_count += 1
        return memoryview(self.raw_buffer)[:requested_length]

    def release(self):
        self.reference_count = max(0, self.reference_count - 1)
        if self.reference_count == 0:
            self.is_allocated = False
            self.allocated_length = 0


class AlignedMemoryPool:
    """Manages pools of pre-allocated fixed-size memory chunks."""
    def __init__(self, chunk_size: int = 4096, initial_chunks: int = 64):
        self.chunk_size = chunk_size
        self.chunks: list[MemoryPoolChunk] = [
            MemoryPoolChunk(i, chunk_size) for i in range(initial_chunks)
        ]
        self.total_allocations = 0
        self.total_deallocations = 0

    def allocate(self, size: int) -> tuple[int, memoryview]:
        for chunk in self.chunks:
            if not chunk.is_allocated:
                mv = chunk.acquire(size)
                self.total_allocations += 1
                return chunk.chunk_id, mv
        # Expand pool dynamically
        new_id = len(self.chunks)
        new_chunk = MemoryPoolChunk(new_id, self.chunk_size)
        self.chunks.append(new_chunk)
        mv = new_chunk.acquire(size)
        self.total_allocations += 1
        return new_id, mv

    def free(self, chunk_id: int):
        if 0 <= chunk_id < len(self.chunks):
            self.chunks[chunk_id].release()
            self.total_deallocations += 1

    def get_utilization_ratio(self) -> float:
        active = sum(1 for c in self.chunks if c.is_allocated)
        return active / len(self.chunks) if self.chunks else 0.0
