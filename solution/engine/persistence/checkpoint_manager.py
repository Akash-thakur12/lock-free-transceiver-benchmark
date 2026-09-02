"""Crash-Recovery Checkpoint Manager & Deterministic State Serializer."""
import json
import zlib

class CheckpointManager:
    """Manages binary state snapshots and idempotent deduplication."""
    def __init__(self):
        self.committed_history: set[tuple[int, int]] = set()  # set of (stream_id, seq_no)

    def record_commit(self, stream_id: int, seq_no: int):
        self.committed_history.add((stream_id, seq_no))

    def is_duplicate(self, stream_id: int, seq_no: int) -> bool:
        return (stream_id, seq_no) in self.committed_history

    def serialize_state(self, transceiver_instance) -> bytes:
        """Serializes ring buffer, reassembly windows, watermarks, clock, and committed history."""
        # 1. Ring Buffer slots
        slots_data = []
        for s in transceiver_instance.ring_buffer.slots:
            slots_data.append({
                "slot_idx": s.slot_idx,
                "current_lease_id": s.current_lease_id,
                "lease_epoch": s.lease_epoch,
                "stream_id": s.stream_id,
                "sequence_no": s.sequence_no,
                "priority": s.priority,
                "lease_expiry_tick": s.lease_expiry_tick,
                "state": s.state.value,
                "payload_hex": s.payload.hex()
            })

        # 2. Reassembly Windows
        reassembly_data = {}
        for sid, win in transceiver_instance.reassembly.windows.items():
            staged = [{"seq": k, "payload_hex": v.hex()} for k, v in getattr(win.queue, "_buffer", {}).items()]
            reassembly_data[str(sid)] = {
                "expected_seq": win.tracker.expected_seq,
                "is_initialized": win.tracker.is_initialized,
                "staged_packets": staged
            }

        # 3. Watermarks
        watermark_data = {
            "high": {str(k): v for k, v in transceiver_instance.watermarks.high_watermarks.items()},
            "low": {str(k): v for k, v in transceiver_instance.watermarks.low_watermarks.items()}
        }

        # 4. Committed History
        history_list = [[sid, sq] for (sid, sq) in self.committed_history]

        state_dict = {
            "version": 1,
            "clock_tick": transceiver_instance.clock.current_tick,
            "next_lease_id": transceiver_instance.ring_buffer.next_lease_id,
            "epoch_counter": transceiver_instance.ring_buffer.epoch_counter,
            "dropped_frames": transceiver_instance.ring_buffer.dropped_frames,
            "total_committed_bytes": transceiver_instance.ring_buffer.total_committed_bytes,
            "slots": slots_data,
            "reassembly": reassembly_data,
            "watermarks": watermark_data,
            "history": history_list
        }

        raw_json = json.dumps(state_dict, separators=(",", ":")).encode("utf-8")
        # Compress and add CRC-32 envelope
        compressed = zlib.compress(raw_json, level=6)
        crc32 = zlib.crc32(compressed) & 0xFFFFFFFF
        return b"SNAP" + crc32.to_bytes(4, "big") + compressed

    def deserialize_state(self, transceiver_instance, snapshot_bytes: bytes):
        """Restores complete transceiver internal state from binary snapshot."""
        if len(snapshot_bytes) < 8 or not snapshot_bytes.startswith(b"SNAP"):
            raise ValueError("Invalid snapshot magic header")
        
        expected_crc = int.from_bytes(snapshot_bytes[4:8], "big")
        compressed_body = snapshot_bytes[8:]
        actual_crc = zlib.crc32(compressed_body) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("Snapshot CRC checksum verification failed")

        raw_json = zlib.decompress(compressed_body)
        state_dict = json.loads(raw_json.decode("utf-8"))

        # Restore Clock
        transceiver_instance.clock._current_tick = state_dict["clock_tick"]

        # Restore Ring Buffer
        rb = transceiver_instance.ring_buffer
        rb.next_lease_id = state_dict["next_lease_id"]
        rb.epoch_counter = state_dict["epoch_counter"]
        rb.dropped_frames = state_dict["dropped_frames"]
        rb.total_committed_bytes = state_dict["total_committed_bytes"]
        rb.active_leases.clear()

        from engine.buffer.slot_descriptor import SlotState
        for s_data in state_dict["slots"]:
            idx = s_data["slot_idx"]
            if 0 <= idx < len(rb.slots):
                s = rb.slots[idx]
                s.current_lease_id = s_data["current_lease_id"]
                s.lease_epoch = s_data["lease_epoch"]
                s.stream_id = s_data["stream_id"]
                s.sequence_no = s_data["sequence_no"]
                s.priority = s_data["priority"]
                s.lease_expiry_tick = s_data["lease_expiry_tick"]
                s.state = SlotState(s_data["state"])
                s.payload = bytes.fromhex(s_data["payload_hex"])
                if s.is_uncommitted_lease and s.current_lease_id > 0:
                    rb.active_leases[s.current_lease_id] = (idx, s.lease_epoch)

        # Restore Reassembly Windows
        transceiver_instance.reassembly.windows.clear()
        from engine.reassembly.sliding_window import GaplessSlidingWindow
        for sid_str, win_data in state_dict["reassembly"].items():
            sid = int(sid_str)
            win = GaplessSlidingWindow(sid)
            win.tracker.expected_seq = win_data["expected_seq"]
            win.tracker.is_initialized = win_data["is_initialized"]
            for staged in win_data["staged_packets"]:
                win.queue.buffer_packet(staged["seq"], bytes.fromhex(staged["payload_hex"]))
            transceiver_instance.reassembly.windows[sid] = win

        # Restore Watermarks
        transceiver_instance.watermarks.high_watermarks = {int(k): v for k, v in state_dict["watermarks"]["high"].items()}
        transceiver_instance.watermarks.low_watermarks = {int(k): v for k, v in state_dict["watermarks"]["low"].items()}

        # Restore Committed History
        self.committed_history = {(item[0], item[1]) for item in state_dict["history"]}
