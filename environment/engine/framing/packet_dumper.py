"""Hexdump Formatter & Wire Packet Visualizer."""

def format_hexdump(data: bytes, bytes_per_line: int = 16) -> str:
    """Formats raw byte stream into standard Wireshark-style canonical hex view."""
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i : i + bytes_per_line]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{i:04x}  {hex_str:<{bytes_per_line*3}}  |{ascii_str}|")
    return "\n".join(lines)


def dump_frame_summary(meta: dict) -> str:
    """Generates structured human-readable packet header telemetry summary."""
    return (
        f"[FRAME] MAGIC={meta.get('magic', 0):#010x} | STREAM={meta.get('stream_id', 0)} | "
        f"SEQ={meta.get('sequence_no', 0)} | FLAGS={meta.get('flags', 0):#04x} | "
        f"LEN={meta.get('payload_len', 0)}B | HDR_CRC={meta.get('header_crc', 0):#06x} | "
        f"FRM_CRC={meta.get('frame_crc', 0):#010x}"
    )
