"""CRC-16 Poly 0x1021 Calculator for 18-Byte Header Prefix."""

def compute_header_crc16(header_prefix_18b: bytes) -> int:
    if len(header_prefix_18b) != 18:
        raise ValueError(f"Header prefix for CRC-16 must be exactly 18 bytes, got {len(header_prefix_18b)}")
    crc = 0xFFFF
    for byte in header_prefix_18b:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
