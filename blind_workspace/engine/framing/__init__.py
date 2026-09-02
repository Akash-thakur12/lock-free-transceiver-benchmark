"""Framing & Protocol Package."""
from .exceptions import (
    TransceiverFramingError, InvalidMagicError, HeaderCorruptError,
    PayloadCorruptError, FrameOverflowError
)
from .crc16_checker import compute_header_crc16
from .crc32_checker import compute_frame_crc32
from .frame_validator import validate_magic_and_reserved, validate_payload_size, validate_flags, MAGIC_EXPECTED
from .header_codec import encode_header, decode_header, HEADER_SIZE
from .frame_codec import encode_full_frame, decode_full_frame

__all__ = [
    "TransceiverFramingError", "InvalidMagicError", "HeaderCorruptError",
    "PayloadCorruptError", "FrameOverflowError",
    "compute_header_crc16", "compute_frame_crc32",
    "validate_magic_and_reserved", "validate_payload_size", "validate_flags", "MAGIC_EXPECTED",
    "encode_header", "decode_header", "HEADER_SIZE",
    "encode_full_frame", "decode_full_frame"
]
