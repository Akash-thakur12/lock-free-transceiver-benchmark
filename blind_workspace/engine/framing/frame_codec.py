"""Full Frame Encoder & Decoder with Nested CRC-16 and CRC-32 Validation."""
import struct
from engine.framing.header_codec import encode_header, decode_header, HEADER_SIZE
from engine.framing.crc32_checker import compute_frame_crc32
from engine.framing.exceptions import PayloadCorruptError, FrameOverflowError

def encode_full_frame(stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes:
    header_bytes = encode_header(stream_id, seq_no, flags, len(payload))
    body = header_bytes + payload
    frame_crc32 = compute_frame_crc32(body)
    return body + struct.pack(">I", frame_crc32)

def decode_full_frame(frame_bytes: bytes) -> tuple[dict, bytes]:
    if len(frame_bytes) < HEADER_SIZE + 4:
        raise FrameOverflowError(f"Frame length {len(frame_bytes)} too short to contain header and CRC-32")

    meta = decode_header(frame_bytes[:HEADER_SIZE])
    payload_len = meta["payload_len"]
    total_expected_len = HEADER_SIZE + payload_len + 4

    if len(frame_bytes) < total_expected_len:
        raise FrameOverflowError(f"Frame truncated: expected {total_expected_len} bytes, got {len(frame_bytes)}")

    payload = frame_bytes[HEADER_SIZE : HEADER_SIZE + payload_len]
    expected_crc32 = struct.unpack_from(">I", frame_bytes, HEADER_SIZE + payload_len)[0]
    actual_crc32 = compute_frame_crc32(frame_bytes[: HEADER_SIZE + payload_len])

    if actual_crc32 != expected_crc32:
        raise PayloadCorruptError(f"Frame CRC-32 mismatch: expected {expected_crc32:#010x}, actual {actual_crc32:#010x}")

    meta["frame_crc"] = expected_crc32
    return meta, payload
