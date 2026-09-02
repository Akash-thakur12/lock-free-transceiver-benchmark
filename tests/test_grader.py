"""4-Tier Deterministic Grader Pipeline with Strict Exception Validation."""
import os
import sys
import ast
import json
import importlib
from pathlib import Path

def scan_anti_cheat(engine_dir: str) -> tuple[bool, str]:
    disallowed_imports = {"ctypes", "_ctypes", "mmap", "sqlite3", "lmdb", "leveldb", "requests", "urllib3", "socket", "http"}
    disallowed_calls = {"eval", "exec", "__import__", "compile"}
    
    if os.path.islink(engine_dir):
        return False, "Symlinked engine directory is prohibited"

    for root, _, files in os.walk(engine_dir):
        if os.path.islink(root):
            return False, f"Symlinked directory detected: {root}"
        for file in files:
            if file.endswith(".py"):
                fpath = os.path.join(root, file)
                if os.path.islink(fpath):
                    return False, f"Symlinked source file detected: {fpath}"
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=file)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.split(".")[0] in disallowed_imports:
                                    return False, f"Prohibited library import: {alias.name}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and node.module.split(".")[0] in disallowed_imports:
                                return False, f"Prohibited module import: {node.module}"
                        elif isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id in disallowed_calls:
                                return False, f"Prohibited built-in call: {node.func.id}"
                except Exception as e:
                    return False, f"AST parse error in {file}: {e}"
    return True, "Passed"


def eval_tier1_wire_framing(Transceiver, HeaderCorruptError, PayloadCorruptError, InvalidMagicError, FrameOverflowError) -> float:
    try:
        tx = Transceiver()
        raw = tx.encode_frame(stream_id=42, seq_no=1001, flags=0x01, payload=b"test_payload_123")
        if len(raw) != 20 + 16 + 4:  # 40 bytes
            return 0.0

        meta, payload = tx.decode_frame(raw)
        if meta["magic"] != 0x54585258 or meta["stream_id"] != 42 or meta["sequence_no"] != 1001 or payload != b"test_payload_123":
            return 0.0

        # Boundary checks: 4096 succeeds, 4097 raises STRICT FrameOverflowError
        tx.encode_frame(stream_id=1, seq_no=1, flags=0, payload=b"A"*4096)
        try:
            tx.encode_frame(stream_id=1, seq_no=1, flags=0, payload=b"A"*4097)
            return 0.0
        except FrameOverflowError:
            pass  # STRICT exception match

        # Header CRC corruption trap
        b_hdr = bytearray(raw)
        b_hdr[2] ^= 0xFF
        try:
            tx.decode_frame(bytes(b_hdr))
            return 0.0
        except HeaderCorruptError:
            pass  # STRICT exception match

        # Frame CRC corruption trap
        b_body = bytearray(raw)
        b_body[25] ^= 0xFF
        try:
            tx.decode_frame(bytes(b_body))
            return 0.0
        except PayloadCorruptError:
            pass  # STRICT exception match

        # Invalid Magic trap
        b_magic = bytearray(raw)
        b_magic[0] = 0x00
        try:
            tx.decode_frame(bytes(b_magic))
            return 0.0
        except (InvalidMagicError, HeaderCorruptError):
            pass

        return 0.250
    except Exception:
        return 0.0


def eval_tier2_mpmc_ring_buffer(Transceiver) -> float:
    try:
        tx = Transceiver(capacity=64, backpressure="BLOCK")
        for seq in range(32):
            if not tx.publish(stream_id=10, seq_no=seq, priority=0, payload=f"block_{seq}".encode("ascii")):
                return 0.0

        drained = tx.poll_stream(10)
        if len(drained) != 32:
            return 0.0
        for seq, (r_seq, r_data) in enumerate(drained):
            if r_seq != seq or r_data != f"block_{seq}".encode("ascii"):
                return 0.0

        # Wraparound boundary test across uint64 edge (2^64-5 to 5)
        base = 18446744073709551610
        tx.publish(stream_id=20, seq_no=base, priority=0, payload=b"wrap_packet")
        r_wrap = tx.poll_stream(20)
        if not r_wrap or r_wrap[0] != (base, b"wrap_packet"):
            return 0.0

        return 0.250
    except Exception:
        return 0.0


def eval_tier3_reassembly_and_telemetry(Transceiver) -> float:
    try:
        tx = Transceiver(capacity=64, backpressure="BLOCK")

        # Initialize stream 7 with sequence 1
        tx.publish(stream_id=7, seq_no=1, priority=0, payload=b"packet_1")
        r1 = tx.poll_stream(7)
        if r1 != [(1, b"packet_1")]:
            return 0.0

        # Now publish seq 3 (without seq 2) -> poll MUST return [] because seq 2 is missing!
        tx.publish(stream_id=7, seq_no=3, priority=0, payload=b"packet_3")
        r_premature = tx.poll_stream(7)
        if len(r_premature) != 0:
            return 0.0  # VIOLATED GAPLESS CONTRACT!

        # Publish missing seq 2 -> poll must now emit BOTH seq 2 and seq 3 in contiguous order
        tx.publish(stream_id=7, seq_no=2, priority=0, payload=b"packet_2")
        res = tx.poll_stream(7)
        if len(res) != 2 or res[0] != (2, b"packet_2") or res[1] != (3, b"packet_3"):
            return 0.0

        # Telemetry validation
        stats = tx.get_telemetry()
        required_keys = {"total_frames", "dropped_frames", "committed_bytes", "p50_latency_ticks", "p99_latency_ticks"}
        if not required_keys.issubset(stats.keys()):
            return 0.0
        if stats["committed_bytes"] <= 0 or stats["total_frames"] < 2:
            return 0.0

        return 0.250
    except Exception:
        return 0.0


def eval_tier4_matrix_stress(Transceiver) -> tuple[float, int]:
    tests_dir = Path(__file__).resolve().parent
    if str(tests_dir.parent) not in sys.path:
        sys.path.insert(0, str(tests_dir.parent))
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    try:
        from tests.generate_matrix import TestMatrixGenerator
    except ImportError:
        from generate_matrix import TestMatrixGenerator

    passed = 0
    for scenario in range(24):
        for var_id in range(100):
            if TestMatrixGenerator.run_case(Transceiver, scenario, var_id):
                passed += 1
    score = (passed / 2400.0) * 0.250
    return score, passed


def run_grader(engine_dir: str) -> dict:
    is_clean, msg = scan_anti_cheat(engine_dir)
    if not is_clean:
        return {"tier1_framing": 0.0, "tier2_mpmc": 0.0, "tier3_reassembly": 0.0, "tier4_matrix": 0.0, "matrix_passed": 0, "matrix_total": 2400, "score": 0.0, "error": msg}

    for mod_name in list(sys.modules.keys()):
        if mod_name == "engine" or mod_name.startswith("engine."):
            del sys.modules[mod_name]

    parent_dir = str(Path(engine_dir).parent)
    if parent_dir in sys.path:
        sys.path.remove(parent_dir)
    sys.path.insert(0, parent_dir)

    try:
        tx_mod = importlib.import_module("engine.transceiver")
        codec_mod = importlib.import_module("engine.framing")
        Transceiver = getattr(tx_mod, "Transceiver")
        HeaderCorruptError = getattr(codec_mod, "HeaderCorruptError")
        PayloadCorruptError = getattr(codec_mod, "PayloadCorruptError")
        InvalidMagicError = getattr(codec_mod, "InvalidMagicError")
        FrameOverflowError = getattr(codec_mod, "FrameOverflowError")
    except Exception as e:
        return {"tier1_framing": 0.0, "tier2_mpmc": 0.0, "tier3_reassembly": 0.0, "tier4_matrix": 0.0, "matrix_passed": 0, "matrix_total": 2400, "score": 0.0, "error": str(e)}

    print("=== EXECUTING 4-TIER LOCK-FREE TRANSCEIVER GRADER ===")
    t1 = eval_tier1_wire_framing(Transceiver, HeaderCorruptError, PayloadCorruptError, InvalidMagicError, FrameOverflowError)
    print(f"  [TIER 1] Wire Framing & Nested CRC : {t1:.3f} / 0.250")

    t2 = eval_tier2_mpmc_ring_buffer(Transceiver)
    print(f"  [TIER 2] MPMC Ring Buffer & Turn    : {t2:.3f} / 0.250")

    t3 = eval_tier3_reassembly_and_telemetry(Transceiver)
    print(f"  [TIER 3] Reassembly & Telemetry     : {t3:.3f} / 0.250")

    t4, m_passed = eval_tier4_matrix_stress(Transceiver)
    print(f"  [TIER 4] 2,400-State Matrix Stress  : {t4:.3f} / 0.250 ({m_passed}/2400 passed)")

    total_score = t1 + t2 + t3 + t4
    return {
        "tier1_framing": round(t1, 3),
        "tier2_mpmc": round(t2, 3),
        "tier3_reassembly": round(t3, 3),
        "tier4_matrix": round(t4, 3),
        "matrix_passed": m_passed,
        "matrix_total": 2400,
        "score": round(total_score, 4)
    }

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "/app/engine"
    res = run_grader(target)
    print("\n" + json.dumps(res, indent=2))
    print(f"\n[REWARD] FINAL COMPOSITE SCORE: {res['score']:.4f}")

if __name__ == "__main__":
    main()
