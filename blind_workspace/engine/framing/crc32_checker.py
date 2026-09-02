"""CRC-32 IEEE 802.3 Calculator for Header + Payload."""
import zlib

def compute_frame_crc32(header_and_payload_bytes: bytes) -> int:
    return zlib.crc32(header_and_payload_bytes) & 0xFFFFFFFF
