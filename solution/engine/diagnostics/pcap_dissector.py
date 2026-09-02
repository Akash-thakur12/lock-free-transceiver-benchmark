"""High-Throughput Binary PCAP Dissector & Packet Inspector."""
import struct
from pathlib import Path

class PCAPDissector:
    """Parses binary PCAP files containing raw Transceiver wire frames."""
    def __init__(self, pcap_path: str):
        self.pcap_path = Path(pcap_path)
        self.total_packets_parsed = 0
        self.total_bytes_parsed = 0

    def parse_frames(self, max_frames: int = 1000) -> list[tuple[dict, bytes]]:
        if not self.pcap_path.exists():
            raise FileNotFoundError(f"PCAP file not found: {self.pcap_path}")

        frames = []
        with open(self.pcap_path, "rb") as f:
            # Skip 24-byte PCAP Global Header
            global_hdr = f.read(24)
            if len(global_hdr) < 24:
                return []

            while len(frames) < max_frames:
                pkt_hdr = f.read(16)
                if len(pkt_hdr) < 16:
                    break
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", pkt_hdr)
                frame_data = f.read(incl_len)
                if len(frame_data) < incl_len:
                    break

                self.total_packets_parsed += 1
                self.total_bytes_parsed += incl_len

                if len(frame_data) >= 24:
                    meta = {
                        "ts_sec": ts_sec,
                        "ts_usec": ts_usec,
                        "frame_len": incl_len,
                        "magic": struct.unpack_from(">I", frame_data, 0)[0],
                        "stream_id": struct.unpack_from(">H", frame_data, 6)[0],
                        "seq_no": struct.unpack_from(">Q", frame_data, 8)[0],
                    }
                    frames.append((meta, frame_data))

        return frames
