"""Combinatorial Evaluation Matrix (3,300 States across 33 Invariant Topologies)."""
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

            elif scenario == 9:
                start_seq = var_id * 10
                tx.publish(stream_id=1, seq_no=start_seq, priority=0, payload=b"packet_0")
                r0 = tx.poll_stream(1)
                if r0 != [(start_seq, b"packet_0")]:
                    return False
                tx.publish(stream_id=1, seq_no=start_seq + 2, priority=0, payload=b"packet_2")
                r_gap = tx.poll_stream(1)
                if len(r_gap) != 0:
                    return False
                tx.publish(stream_id=1, seq_no=start_seq + 1, priority=0, payload=b"packet_1")
                r_flush = tx.poll_stream(1)
                if len(r_flush) != 2 or r_flush[0][1] != b"packet_1" or r_flush[1][1] != b"packet_2":
                    return False

            elif scenario == 10:
                p_tx = transceiver_cls(capacity=2, backpressure="BLOCK")
                p_tx.publish(stream_id=1, seq_no=1, priority=0, payload=b"committed_01")
                p_tx.publish(stream_id=1, seq_no=2, priority=0, payload=b"committed_02")
                res_high = p_tx.publish(stream_id=2, seq_no=1, priority=3, payload=data)
                if res_high is not False:
                    return False
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

            elif scenario == 15:
                for s in range(5):
                    tx.publish(stream_id=s+1, seq_no=s, priority=1, payload=data)
                    tx.step_clock(1)
                for s in range(5):
                    r = tx.poll_stream(s+1)
                    if not r:
                        return False

            elif scenario == 16:
                tx.schedule_fiber(task_id=1, priority=0, work_fn=lambda: "low")
                tx.schedule_fiber(task_id=2, priority=3, work_fn=lambda: "high")
                executed_p = tx.step_fibers()
                if executed_p != 3:
                    return False

            elif scenario == 17:
                for s in range(10):
                    tx.publish(stream_id=5, seq_no=s, priority=0, payload=b"A"*16)
                lag_before = tx.get_watermark_lag(5)
                if lag_before < 9:
                    return False
                tx.poll_stream(5)
                lag_after = tx.get_watermark_lag(5)
                if lag_after != 0:
                    return False

            elif scenario == 18:
                results = []
                for p in range(4):
                    tx.schedule_fiber(task_id=p, priority=p, work_fn=lambda p=p: results.append(p))
                while tx.step_fibers() != -1:
                    pass
                if results != [3, 2, 1, 0]:
                    return False

            elif scenario == 19:
                tx.publish(stream_id=1, seq_no=100, priority=0, payload=data)
                tx.publish(stream_id=2, seq_no=200, priority=0, payload=data)
                if tx.get_watermark_lag(1) != 0 or tx.get_watermark_lag(2) != 0:
                    pass
                tx.publish(stream_id=1, seq_no=105, priority=0, payload=data)
                if tx.get_watermark_lag(1) != 5:
                    return False

            elif scenario == 20:
                def failing_fiber():
                    raise RuntimeError("Fiber Crash")
                tx.schedule_fiber(task_id=10, priority=2, work_fn=failing_fiber)
                tx.schedule_fiber(task_id=11, priority=1, work_fn=lambda: "ok")
                p1 = tx.step_fibers()
                p2 = tx.step_fibers()
                if p1 != 2 or p2 != 1:
                    return False

            elif scenario == 21:
                tx.schedule_fiber(task_id=1, priority=0, work_fn=lambda: "t1")
                tx.step_fibers()
                tx.schedule_fiber(task_id=2, priority=2, work_fn=lambda: "t2")
                tx.schedule_fiber(task_id=3, priority=3, work_fn=lambda: "t3")
                if tx.step_fibers() != 3 or tx.step_fibers() != 2:
                    return False

            elif scenario == 22:
                for sid in range(1, 5):
                    for sq in range(5):
                        tx.publish(stream_id=sid, seq_no=sq, priority=0, payload=b"M"*8)
                for sid in range(1, 5):
                    if tx.get_watermark_lag(sid) != 4:
                        return False
                    tx.poll_stream(sid)
                    if tx.get_watermark_lag(sid) != 0:
                        return False

            elif scenario == 23:
                for s in range(10):
                    tx.publish(stream_id=1, seq_no=s, priority=s%4, payload=data)
                    tx.schedule_fiber(task_id=s, priority=s%4, work_fn=lambda s=s: s*2)
                while tx.step_fibers() != -1:
                    pass
                t = tx.get_telemetry()
                if t.get("total_frames", 0) < 10 or t.get("p50_latency_ticks", 0) <= 0:
                    return False

            # S24: Snapshot & Restore State Roundtrip
            elif scenario == 24:
                tx.publish(stream_id=1, seq_no=var_id, priority=0, payload=data)
                snap = tx.snapshot()
                if not snap or not isinstance(snap, bytes) or len(snap) < 16:
                    return False
                # Restore onto fresh instance
                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)
                drained = fresh_tx.poll_stream(1)
                if len(drained) != 1 or drained[0] != (var_id, data):
                    return False

            # S25: Post-Restore Idempotent Duplicate Rejection
            elif scenario == 25:
                tx.publish(stream_id=2, seq_no=var_id, priority=1, payload=data)
                snap = tx.snapshot()
                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)
                # Re-publishing the exact same (stream_id, seq_no) MUST be rejected as duplicate
                dup_res = fresh_tx.publish(stream_id=2, seq_no=var_id, priority=1, payload=data)
                if dup_res is not False:
                    return False
                # Draining still yields original uncorrupted packet
                drained = fresh_tx.poll_stream(2)
                if len(drained) != 1 or drained[0] != (var_id, data):
                    return False

            # S26: Checkpoint Restoration of Out-of-Order Staging Window
            elif scenario == 26:
                # Stage out-of-order sequence (gap at seq 1)
                tx.publish(stream_id=3, seq_no=var_id * 10, priority=0, payload=b"p0")
                tx.poll_stream(3)
                tx.publish(stream_id=3, seq_no=var_id * 10 + 2, priority=0, payload=b"p2")
                snap = tx.snapshot()

                # Restore into fresh instance
                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)

                # Poll returns empty because gap (seq + 1) is still missing
                if len(fresh_tx.poll_stream(3)) != 0:
                    return False

                # Publish missing gap -> must emit both [p1, p2]
                fresh_tx.publish(stream_id=3, seq_no=var_id * 10 + 1, priority=0, payload=b"p1")
                drained = fresh_tx.poll_stream(3)
                if len(drained) != 2 or drained[0][1] != b"p1" or drained[1][1] != b"p2":
                    return False

            # S27: Watermark Continuity Across Checkpoint
            elif scenario == 27:
                for sq in range(6):
                    tx.publish(stream_id=4, seq_no=sq, priority=0, payload=b"W"*16)
                snap = tx.snapshot()
                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)
                if fresh_tx.get_watermark_lag(4) != 5:
                    return False
                fresh_tx.poll_stream(4)
                if fresh_tx.get_watermark_lag(4) != 0:
                    return False

            # S28: Ring Buffer Slot Lease State Restoration
            elif scenario == 28:
                tx.publish(stream_id=1, seq_no=10, priority=0, payload=b"s1")
                tx.publish(stream_id=1, seq_no=11, priority=0, payload=b"s2")
                snap = tx.snapshot()
                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)
                # Next publish should get subsequent sequence without collision
                if not fresh_tx.publish(stream_id=1, seq_no=12, priority=0, payload=b"s3"):
                    return False
                drained = fresh_tx.poll_stream(1)
                if len(drained) != 3:
                    return False

            # S29: Multi-Stream Checkpoint Isolation
            elif scenario == 29:
                tx.publish(stream_id=10, seq_no=1, priority=0, payload=b"data_a")
                tx.publish(stream_id=20, seq_no=2, priority=0, payload=b"data_b")
                tx.poll_stream(10)  # Drain stream 10, leave stream 20 unconsumed
                snap = tx.snapshot()

                fresh_tx = transceiver_cls(capacity=128)
                fresh_tx.restore(snap)
                # Stream 10 is already consumed (returns empty)
                if len(fresh_tx.poll_stream(10)) != 0:
                    return False
                # Stream 20 is still unconsumed
                d20 = fresh_tx.poll_stream(20)
                if len(d20) != 1 or d20[0] != (2, b"data_b"):
                    return False

            # S30: Snapshot Checksum Corrupt Rejection
            elif scenario == 30:
                tx.publish(stream_id=1, seq_no=1, priority=0, payload=data)
                snap = bytearray(tx.snapshot())
                snap[6] ^= 0xFF  # Corrupt CRC byte
                fresh_tx = transceiver_cls(capacity=128)
                try:
                    fresh_tx.restore(bytes(snap))
                    return False
                except ValueError:
                    pass

            # S31: Multi-Cycle Checkpoint Load
            elif scenario == 31:
                for cycle in range(3):
                    tx.publish(stream_id=1, seq_no=cycle, priority=0, payload=data)
                    snap = tx.snapshot()
                    tx = transceiver_cls(capacity=128)
                    tx.restore(snap)
                drained = tx.poll_stream(1)
                if len(drained) != 3:
                    return False

            # S32: REJECT Backpressure Immediate Rejection
            else:
                rej_tx = transceiver_cls(capacity=4, backpressure="REJECT")
                for s in range(4):
                    if not rej_tx.publish(stream_id=1, seq_no=s, priority=0, payload=b"fill_" + bytes([s])):
                        return False
                # 5th publish into saturated REJECT buffer MUST return False immediately
                rej_res = rej_tx.publish(stream_id=1, seq_no=4, priority=0, payload=b"overflow")
                if rej_res is not False:
                    return False
                # Original 4 committed slots must remain 100% intact and pollable
                drained = rej_tx.poll_stream(1)
                if len(drained) != 4 or [p[0] for p in drained] != [0, 1, 2, 3]:
                    return False

            return True
        except Exception:
            return False
