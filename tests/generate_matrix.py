"""Combinatorial Evaluation Matrix (1,600 States with Hardened S09 and S10 Traps)."""
from engine.framing import HeaderCorruptError, PayloadCorruptError, InvalidMagicError, FrameOverflowError

class TestMatrixGenerator:
    @staticmethod
    def get_payload_variant(s_id: int, var_id: int) -> bytes:
        if var_id % 5 == 0:
            return f"stream_block_{s_id}_{var_id}".encode("ascii")
        elif var_id % 5 == 1:
            return bytes([(s_id + var_id + i) % 256 for i in range(32)])
        elif var_id % 5 == 2:
            return b"\x00" * 64
        elif var_id % 5 == 3:
            return f"🔒_stream_payload_{s_id}_{var_id}_🚀".encode("utf-8")
        else:
            return (f"large_stream_block_{s_id}_" + "X" * 128)[:128].encode("ascii")

    @staticmethod
    def run_case(transceiver_cls, scenario: int, var_id: int) -> bool:
        try:
            tx = transceiver_cls(capacity=128, backpressure="BLOCK")
            data = TestMatrixGenerator.get_payload_variant(scenario, var_id)

            if scenario == 0:
                seq = var_id
                if not tx.publish(stream_id=1, seq_no=seq, priority=0, payload=data):
                    return False
                res = tx.poll_stream(1)
                if not res or res[0] != (seq, data):
                    return False

            elif scenario == 1:
                seq = var_id * 2
                tx.publish(stream_id=1, seq_no=seq, priority=1, payload=data)
                tx.publish(stream_id=2, seq_no=seq, priority=1, payload=data)
                r1 = tx.poll_stream(1)
                r2 = tx.poll_stream(2)
                if not r1 or not r2 or r1[0][1] != data or r2[0][1] != data:
                    return False

            elif scenario == 2:
                for p in range(4):
                    tx.publish(stream_id=p+1, seq_no=var_id, priority=1, payload=data)
                for p in range(4):
                    r = tx.poll_stream(p+1)
                    if not r or r[0][1] != data:
                        return False

            elif scenario == 3:
                tx.publish(stream_id=5, seq_no=var_id, priority=0, payload=data)
                r = tx.poll_stream(5)
                if not r or r[0][1] != data:
                    return False
                if len(tx.poll_stream(5)) != 0:
                    return False

            elif scenario == 4:
                sid = (var_id % 16) + 1
                tx.publish(stream_id=sid, seq_no=var_id, priority=1, payload=data)
                r = tx.poll_stream(sid)
                if not r or r[0][1] != data:
                    return False

            elif scenario == 5:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                corrupted = bytearray(enc)
                corrupted[2] ^= 0xFF
                try:
                    tx.decode_frame(bytes(corrupted))
                    return False
                except HeaderCorruptError:
                    pass

            elif scenario == 6:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                corrupted = bytearray(enc)
                corrupted[22] ^= 0xFF
                try:
                    tx.decode_frame(bytes(corrupted))
                    return False
                except PayloadCorruptError:
                    pass

            elif scenario == 7:
                small_tx = transceiver_cls(capacity=4, backpressure="DROP_OLDEST")
                for s in range(8):
                    small_tx.publish(stream_id=1, seq_no=s, priority=0, payload=b"X"*16)
                t = small_tx.get_telemetry()
                if t.get("dropped_frames", 0) < 1:
                    return False

            elif scenario == 8:
                base_seq = 18446744073709551600 + (var_id % 10)
                tx.publish(stream_id=1, seq_no=base_seq, priority=0, payload=data)
                r = tx.poll_stream(1)
                if not r or r[0] != (base_seq, data):
                    return False

            # S09: STRICT GAPLESS REASSEMBLY WITH MISSING GAP
            elif scenario == 9:
                start_seq = var_id * 10
                # Publish sequence start_seq
                tx.publish(stream_id=1, seq_no=start_seq, priority=0, payload=b"packet_0")
                r0 = tx.poll_stream(1)
                if r0 != [(start_seq, b"packet_0")]:
                    return False

                # Publish sequence start_seq + 2 (without start_seq + 1)
                tx.publish(stream_id=1, seq_no=start_seq + 2, priority=0, payload=b"packet_2")
                # Poll MUST return [] because start_seq + 1 is missing!
                r_gap = tx.poll_stream(1)
                if len(r_gap) != 0:
                    return False  # Violated gapless contract!

                # Publish the missing start_seq + 1 -> now must emit both (start_seq+1) and (start_seq+2)
                tx.publish(stream_id=1, seq_no=start_seq + 1, priority=0, payload=b"packet_1")
                r_flush = tx.poll_stream(1)
                if len(r_flush) != 2 or r_flush[0][1] != b"packet_1" or r_flush[1][1] != b"packet_2":
                    return False

            # S10: STRICT PREEMPTION INVARIANT (NEVER DESTROY COMMITTED DATA)
            elif scenario == 10:
                p_tx = transceiver_cls(capacity=2, backpressure="BLOCK")
                # Fill buffer with 2 COMMITTED packets
                p_tx.publish(stream_id=1, seq_no=1, priority=0, payload=b"committed_01")
                p_tx.publish(stream_id=1, seq_no=2, priority=0, payload=b"committed_02")

                # Try to publish high-priority packet when buffer is full of COMMITTED data.
                # Under BLOCK policy, it CANNOT preempt committed data -> must return False!
                res_high = p_tx.publish(stream_id=2, seq_no=1, priority=3, payload=data)
                if res_high is not False:
                    return False  # Overwrote committed data!

                # Draining stream 1 must return BOTH original committed packets intact!
                drained = p_tx.poll_stream(1)
                if len(drained) != 2 or drained[0][1] != b"committed_01" or drained[1][1] != b"committed_02":
                    return False

            elif scenario == 11:
                large_blob = b"B" * 4096
                if not tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=large_blob):
                    return False
                r = tx.poll_stream(1)
                if not r or len(r[0][1]) != 4096:
                    return False

            elif scenario == 12:
                if not tx.publish(stream_id=99, seq_no=var_id, priority=0, payload=data):
                    return False
                r = tx.poll_stream(99)
                if not r or r[0][1] != data:
                    return False
                if len(tx.poll_stream(99)) != 0:
                    return False

            elif scenario == 13:
                enc = tx.encode_frame(stream_id=1, seq_no=var_id, flags=0, payload=data)
                bad_magic = bytearray(enc)
                bad_magic[0] = 0x00
                try:
                    tx.decode_frame(bytes(bad_magic))
                    return False
                except (InvalidMagicError, HeaderCorruptError):
                    pass

            elif scenario == 14:
                tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=data)
                t = tx.get_telemetry()
                if "p50_latency_ticks" not in t or t.get("committed_bytes", 0) <= 0:
                    return False

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
