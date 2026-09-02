"""Binary Wire Framing Codec & Exceptions."""
import struct
from engine.crc import compute_crc16, compute_crc32

MAGIC_EXPECTED = 0x54585258  # 'TXRX'

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
    payload_len = len(payload)
    if payload_len > 4096:
        raise FrameOverflowError(f"Payload size {payload_len} exceeds maximum 4096 bytes")

    # Header without CRC (18 bytes)
    partial_hdr = struct.pack(">IBBHQH", MAGIC_EXPECTED, flags, 0x00, stream_id, seq_no, payload_len)
    hdr_crc = compute_crc16(partial_hdr)
    full_hdr = partial_hdr + struct.pack(">H", hdr_crc)

    # Frame payload & trailing CRC-32
    body = full_hdr + payload
    frame_crc = compute_crc32(body)
    return body + struct.pack(">I", frame_crc)


def decode_frame(frame_bytes: bytes) -> tuple[dict, bytes]:
    if len(frame_bytes) < 24:
        raise FrameOverflowError("Frame bytes too short (< 24 bytes)")

    # 1. Verify Header CRC-16 over first 18 bytes
    partial_hdr = frame_bytes[:18]
    expected_hdr_crc = struct.unpack_from(">H", frame_bytes, 18)[0]
    actual_hdr_crc = compute_crc16(partial_hdr)
    if actual_hdr_crc != expected_hdr_crc:
        raise HeaderCorruptError(f"Header CRC-16 mismatch: expected {expected_hdr_crc:#06x}, actual {actual_hdr_crc:#06x}")

    magic, flags, reserved, stream_id, seq_no, payload_len = struct.unpack(">IBBHQH", partial_hdr)
    if magic != MAGIC_EXPECTED:
        raise InvalidMagicError(f"Invalid magic word: {magic:#010x}")
    if reserved != 0x00:
        raise InvalidMagicError(f"Reserved field must be 0x00, got {reserved:#04x}")
    if payload_len > 4096:
        raise FrameOverflowError(f"Declared payload len {payload_len} exceeds 4096")

    total_expected_len = 20 + payload_len + 4
    if len(frame_bytes) < total_expected_len:
        raise FrameOverflowError(f"Frame truncated: expected {total_expected_len} bytes, got {len(frame_bytes)}")

    payload = frame_bytes[20 : 20 + payload_len]
    expected_frame_crc = struct.unpack_from(">I", frame_bytes, 20 + payload_len)[0]
    actual_frame_crc = compute_crc32(frame_bytes[: 20 + payload_len])
    if actual_frame_crc != expected_frame_crc:
        raise PayloadCorruptError(f"Frame CRC-32 mismatch: expected {expected_frame_crc:#010x}, actual {actual_frame_crc:#010x}")

    meta = {
        "magic": magic,
        "flags": flags,
        "stream_id": stream_id,
        "sequence_no": seq_no,
        "payload_len": payload_len,
        "header_crc": expected_hdr_crc,
        "frame_crc": expected_frame_crc
    }
    return meta, payload
