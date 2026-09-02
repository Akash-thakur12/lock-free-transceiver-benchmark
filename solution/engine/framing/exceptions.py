"""Framing & Protocol Exception Hierarchy."""

class TransceiverFramingError(Exception):
    """Base exception for all transceiver framing errors."""
    pass

class InvalidMagicError(TransceiverFramingError):
    """Raised when frame MAGIC word or reserved byte is invalid."""
    pass

class HeaderCorruptError(TransceiverFramingError):
    """Raised when Header CRC-16 [0:18] checksum validation fails."""
    pass

class PayloadCorruptError(TransceiverFramingError):
    """Raised when Frame CRC-32 [0:20+N] checksum validation fails."""
    pass

class FrameOverflowError(TransceiverFramingError):
    """Raised when payload exceeds 4096 bytes or frame bytes truncated."""
    pass
