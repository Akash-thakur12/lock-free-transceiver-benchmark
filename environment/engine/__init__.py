"""Lock-Free Transceiver Starter Scaffold."""
from .transceiver import Transceiver
from .codec import (
    TransceiverError, InvalidMagicError, HeaderCorruptError,
    PayloadCorruptError, FrameOverflowError, BufferOverflowError,
    SlotStateViolationError, encode_frame, decode_frame
)

__all__ = [
    "Transceiver", "TransceiverError", "InvalidMagicError",
    "HeaderCorruptError", "PayloadCorruptError", "FrameOverflowError",
    "BufferOverflowError", "SlotStateViolationError",
    "encode_frame", "decode_frame"
]
