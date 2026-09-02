"""20-Byte Big-Endian Header Encoder & Decoder."""
import struct
from engine.framing.crc16_checker import compute_header_crc16
from engine.framing.frame_validator import validate_magic_and_reserved, validate_payload_size, MAGIC_EXPECTED
from engine.framing.exceptions import HeaderCorruptError, FrameOverflowError

# 20-Byte Layout: MAGIC(4B) + flags(1B) + reserved(1B) + stream_id(2B) + seq_no(8B) + payload_len(2B) + header_crc(2B)
HEADER_FORMAT = ">IBBHQHH"
HEADER_SIZE = 20

def encode_header(stream_id: int, seq_no: int, flags: int, payload_len: int) -> bytes:
    validate_payload_size(payload_len)
    partial_18b = struct.pack(">IBBHQH", MAGIC_EXPECTED, flags, 0x00, stream_id, seq_no, payload_len)
    hdr_crc16 = compute_header_crc16(partial_18b)
    return partial_18b + struct.pack(">H", hdr_crc16)

def decode_header(header_20b: bytes) -> dict:
    if len(header_20b) < HEADER_SIZE:
        raise FrameOverflowError(f"Header truncated: expected {HEADER_SIZE} bytes, got {len(header_20b)}")

    partial_18b = header_20b[:18]
    expected_crc16 = struct.unpack_from(">H", header_20b, 18)[0]
    actual_crc16 = compute_header_crc16(partial_18b)
    if actual_crc16 != expected_crc16:
        raise HeaderCorruptError(f"Header CRC-16 mismatch: expected {expected_crc16:#06x}, actual {actual_crc16:#06x}")

    magic, flags, reserved, stream_id, seq_no, payload_len = struct.unpack(">IBBHQH", partial_18b)
    validate_magic_and_reserved(magic, reserved)
    validate_payload_size(payload_len)

    return {
        "magic": magic,
        "flags": flags,
        "reserved": reserved,
        "stream_id": stream_id,
        "sequence_no": seq_no,
        "payload_len": payload_len,
        "header_crc": expected_crc16
    }
