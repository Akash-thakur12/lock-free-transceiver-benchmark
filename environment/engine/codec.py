"""Binary Wire Framing Codec Starter Scaffold."""

class TransceiverError(Exception):
    pass

class InvalidMagicError(TransceiverError):
    pass

class HeaderCorruptError(TransceiverError):
    pass

class PayloadCorruptError(TransceiverError):
    pass

class FrameOverflowError(TransceiverError):
    pass

class BufferOverflowError(TransceiverError):
    pass

class SlotStateViolationError(TransceiverError):
    pass

def encode_frame(stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes:
    return b""

def decode_frame(frame_bytes: bytes) -> tuple[dict, bytes]:
    return {}, b""
