"""Lock-Free Transceiver Package."""
from .transceiver import Transceiver
from .framing import (
    TransceiverFramingError, InvalidMagicError, HeaderCorruptError,
    PayloadCorruptError, FrameOverflowError
)
from .buffer import BufferError, BufferOverflowError, SlotStateViolationError

TransceiverError = TransceiverFramingError

__all__ = [
    "Transceiver", "TransceiverError", "TransceiverFramingError",
    "InvalidMagicError", "HeaderCorruptError", "PayloadCorruptError",
    "FrameOverflowError", "BufferError", "BufferOverflowError",
    "SlotStateViolationError"
]
