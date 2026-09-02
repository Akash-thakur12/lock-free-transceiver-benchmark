"""Frame Boundary & Flag Bitmask Validator."""
from engine.framing.exceptions import InvalidMagicError, FrameOverflowError

MAGIC_EXPECTED = 0x54585258  # 'TXRX'
MAX_PAYLOAD_BYTES = 4096

VALID_FLAG_MASK = 0x0F  # 0x01=SYN, 0x02=FIN, 0x04=URG, 0x08=COMPRESSED

def validate_magic_and_reserved(magic: int, reserved: int):
    if magic != MAGIC_EXPECTED:
        raise InvalidMagicError(f"Invalid frame magic {magic:#010x}, expected {MAGIC_EXPECTED:#010x}")
    if reserved != 0x00:
        raise InvalidMagicError(f"Reserved byte must be 0x00, got {reserved:#04x}")

def validate_payload_size(payload_len: int):
    if payload_len < 0 or payload_len > MAX_PAYLOAD_BYTES:
        raise FrameOverflowError(f"Payload size {payload_len} out of valid bounds [0, {MAX_PAYLOAD_BYTES}]")

def validate_flags(flags: int) -> bool:
    return (flags & ~VALID_FLAG_MASK) == 0
