"""Framing Exceptions Starter Scaffold."""

class TransceiverFramingError(Exception):
    pass

class InvalidMagicError(TransceiverFramingError):
    pass

class HeaderCorruptError(TransceiverFramingError):
    pass

class PayloadCorruptError(TransceiverFramingError):
    pass

class FrameOverflowError(TransceiverFramingError):
    pass
