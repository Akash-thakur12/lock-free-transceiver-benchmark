"""Transceiver Starter Scaffold."""
from .transceiver import Transceiver
from .framing import (
    TransceiverFramingError, InvalidMagicError, HeaderCorruptError,
    PayloadCorruptError, FrameOverflowError
)

TransceiverError = TransceiverFramingError

__all__ = [
    "Transceiver", "TransceiverError", "TransceiverFramingError",
    "InvalidMagicError", "HeaderCorruptError", "PayloadCorruptError",
    "FrameOverflowError"
]
