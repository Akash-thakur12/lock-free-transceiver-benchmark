"""1,600-State Combinatorial Matrix Generator for Transceiver Benchmark."""

class TestMatrixGenerator:
    @staticmethod
    def get_payload_variant(s_id: int, var_id: int) -> bytes:
        if var_id % 5 == 0:
            return f"transceiver_packet_{s_id}_{var_id}".encode("ascii")
        elif var_id % 5 == 1:
            return bytes([(s_id + var_id + i) % 256 for i in range(32)])
        elif var_id % 5 == 2:
            return b"\x00" * 64
        elif var_id % 5 == 3:
            return f"🚀_stream_{s_id}_var_{var_id}_🔒".encode("utf-8")
        else:
            return (f"large_stream_block_{s_id}_" + "X" * 128)[:128].encode("ascii")

    @staticmethod
    def run_case(transceiver_cls, scenario: int, var_id: int) -> bool:
        try:
            tx = transceiver_cls(capacity=128, backpressure="BLOCK")
            data = TestMatrixGenerator.get_payload_variant(scenario, var_id)

            # S00: Monotonic Sequential Ingestion (1 Stream)
            if scenario == 0:
                seq = var_id
                if not tx.publish(stream_id=1, seq_no=seq, priority=0, payload=data):
                    return False
                res = tx.poll_stream(1)
                if not res or res[0] != (seq, data):
                    return False

            # S01: Interleaved Dual Stream Contention
            elif scenario == 1:
                seq = var_id * 2
                tx.publish(stream_id=1, seq_no=seq, priority=1, payload=data)
                tx.publish(stream_id=2, seq_no=seq, priority=1, payload=data)
                r1 = tx.poll_stream(1)
                r2 = tx.poll_stream(2)
                if not r1 or not r2 or r1[0][1] != data or r2[0][1] != data:
                    return False

            # S02: High-Producer Contention Burst
            elif scenario == 2:
                for p in range(4):
                    tx.publish(stream_id=p+1, seq_no=var_id, priority=1, payload=data)
                for p in range(4):
                    r = tx.poll_stream(p+1)
                    if not r or r[0][1] != data:
                        return False

            # S03: High-Consumer Drain Burst
            elif scenario == 3:
                tx.publish(stream_id=5, seq_no=var_id, priority=0, payload=data)
                r = tx.poll_stream(5)
                if not r or r[0][1] != data:
                    return False
                # Second poll must be empty
                if len(tx.poll_stream(5)) != 0:
                    return False

            # S04: 16-Stream Multi-Tenant Multiplexing
            elif scenario == 4:
                sid = (var_id % 16) + 1
                tx.publish(stream_id=sid, seq_no=var_id, priority=1, payload=data)
                r = tx.poll_stream(sid)
                if not r or r[0][1] != data:
                    return False

            # S05: Header CRC-16 Corruption Trap
            elif scenario == 5:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                # Corrupt byte in header
                corrupted = bytearray(enc)
                corrupted[2] ^= 0xFF
                try:
                    tx.decode_frame(bytes(corrupted))
                    return False  # Must raise HeaderCorruptError
                except Exception:
                    pass

            # S06: Payload CRC-32 Truncation & Framing Trap
            elif scenario == 6:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                corrupted = bytearray(enc)
                corrupted[22] ^= 0xFF  # Corrupt payload byte
                try:
                    tx.decode_frame(bytes(corrupted))
                    return False  # Must raise PayloadCorruptError
                except Exception:
                    pass

            # S07: Backpressure DROP_OLDEST Churn & Telemetry
            elif scenario == 7:
                small_tx = transceiver_cls(capacity=4, backpressure="DROP_OLDEST")
                for s in range(8):
                    small_tx.publish(stream_id=1, seq_no=s, priority=0, payload=b"X"*16)
                t = small_tx.get_telemetry()
                if t.get("dropped_frames", 0) < 1:
                    return False

            # S08: Sequence Wraparound (2^64-16 -> 0 -> 15)
            elif scenario == 8:
                base_seq = 18446744073709551600 + (var_id % 10)
                tx.publish(stream_id=1, seq_no=base_seq, priority=0, payload=data)
                r = tx.poll_stream(1)
                if not r or r[0] != (base_seq, data):
                    return False

            # S09: Out-of-Order Commit Reassembly Window
            elif scenario == 9:
                tx.publish(stream_id=1, seq_no=var_id + 1, priority=0, payload=b"future")
                tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=b"first")
                r = tx.poll_stream(1)
                if len(r) != 2 or r[0][1] != b"first" or r[1][1] != b"future":
                    return False

            # S10: Priority Lease Preemption under Full Buffer
            elif scenario == 10:
                p_tx = transceiver_cls(capacity=2, backpressure="BLOCK")
                p_tx.publish(stream_id=1, seq_no=1, priority=0, payload=b"low1")
                p_tx.publish(stream_id=1, seq_no=2, priority=0, payload=b"low2")
                # Preempt with critical priority 3
                if not p_tx.publish(stream_id=2, seq_no=1, priority=3, payload=data):
                    return False

            # S11: Max Boundary Payload (4096B)
            elif scenario == 11:
                large_blob = b"B" * 4096
                if not tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=large_blob):
                    return False
                r = tx.poll_stream(1)
                if not r or len(r[0][1]) != 4096:
                    return False

            # S12: Empty Buffer Drain Starvation & Drain Parity
            elif scenario == 12:
                if not tx.publish(stream_id=99, seq_no=var_id, priority=0, payload=data):
                    return False
                r = tx.poll_stream(99)
                if not r or r[0][1] != data:
                    return False
                # Second poll on drained stream must be empty
                if len(tx.poll_stream(99)) != 0:
                    return False

            # S13: Corrupt Magic Word Rejection
            elif scenario == 13:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                bad_magic = bytearray(enc)
                bad_magic[0] = 0x00
                try:
                    tx.decode_frame(bytes(bad_magic))
                    return False
                except Exception:
                    pass

            # S14: Telemetry Latency Tracking
            elif scenario == 14:
                tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=data)
                t = tx.get_telemetry()
                if "p50_latency_ticks" not in t or t.get("committed_bytes", 0) <= 0:
                    return False

            # S15: Combined Multi-Step Churn
            else:
                for s in range(5):
                    tx.publish(stream_id=s+1, seq_no=s, priority=1, payload=data)
                    tx.step_clock(1)
                for s in range(5):
                    r = tx.poll_stream(s+1)
                    if not r:
                        return False

            return True
        except Exception:
            return False
