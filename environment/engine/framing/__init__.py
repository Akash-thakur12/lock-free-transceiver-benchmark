"""Framing Package Starter Scaffold."""
from .exceptions import (
    TransceiverFramingError, InvalidMagicError, HeaderCorruptError,
    PayloadCorruptError, FrameOverflowError
)
from .header_codec import encode_header, decode_header
from .frame_codec import encode_full_frame, decode_full_frame

__all__ = [
    "TransceiverFramingError", "InvalidMagicError", "HeaderCorruptError",
    "PayloadCorruptError", "FrameOverflowError",
    "encode_header", "decode_header",
    "encode_full_frame", "decode_full_frame"
]
