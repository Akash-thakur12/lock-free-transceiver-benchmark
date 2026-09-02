"""CRC-16 and CRC-32 Implementation."""
import zlib

def compute_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def compute_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF
