"""Out-of-Order Packet Buffer Queue."""
from engine.reassembly.exceptions import WindowCapacityOverflowError

MAX_WINDOW_BUFFER_SIZE = 1024

class OutOfOrderQueue:
    def __init__(self, max_size: int = MAX_WINDOW_BUFFER_SIZE):
        self.max_size = max_size
        self._buffer: dict[int, bytes] = {}  # seq_no -> payload

    def buffer_packet(self, seq_no: int, payload: bytes):
        if len(self._buffer) >= self.max_size and seq_no not in self._buffer:
            raise WindowCapacityOverflowError(f"Reassembly window buffer full (>{self.max_size} packets)")
        self._buffer[seq_no] = payload

    def has_seq(self, seq_no: int) -> bool:
        return seq_no in self._buffer

    def pop_seq(self, seq_no: int) -> bytes:
        return self._buffer.pop(seq_no)

    def is_empty(self) -> bool:
        return len(self._buffer) == 0

    def clear(self):
        self._buffer.clear()
