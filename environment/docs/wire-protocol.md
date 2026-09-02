# Wire Protocol Specification
20-Byte Big-Endian Header: MAGIC(4B) + flags(1B) + reserved(1B) + stream_id(2B) + seq_no(8B) + payload_len(2B) + header_crc(2B)
Followed by Payload (N Bytes) and Frame CRC-32 (4B).
