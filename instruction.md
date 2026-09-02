# Task: High-Throughput Lock-Free Ring Buffer & Zero-Copy Transceiver

## Overview
Implement a high-performance, discrete-event packet transceiver engine in Python (`engine/`). The system manages multi-stream binary packet encoding/decoding, lock-free ring buffering with priority preemption, gapless out-of-order reassembly, cooperative fiber scheduling, and microsecond-level telemetry.

---

## 1. Public API Contract (`Transceiver` Class in `engine/transceiver.py`)

The primary entry point is the `Transceiver` class, which MUST expose the following public methods:

```python
class Transceiver:
    def __init__(self, capacity: int = 128, backpressure: str = "BLOCK"):
        """Initializes the transceiver with power-of-two ring buffer capacity and backpressure policy ('BLOCK', 'DROP_OLDEST', 'REJECT')."""
        ...

    def encode_frame(self, stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes:
        """Encodes a 20-byte header + payload + CRC-32 into a binary frame."""
        ...

    def decode_frame(self, frame_bytes: bytes) -> tuple[dict, bytes]:
        """Decodes a binary frame, verifying Header CRC-16 first, then Magic/Flags, then Payload CRC-32.
        
        Returns:
            tuple[dict, bytes]: (metadata_dict, payload_bytes)
            where metadata_dict MUST contain the exact keys:
            {
                "magic": int,          # uint32 MAGIC (0x54585258)
                "flags": int,          # uint8 flags
                "reserved": int,       # uint8 reserved byte (0x00)
                "stream_id": int,      # uint16 stream identifier
                "sequence_no": int,    # uint64 sequence number
                "payload_len": int,    # uint16 payload length in bytes
                "header_crc": int,     # uint16 header CRC-16
                "frame_crc": int       # uint32 full frame CRC-32
            }
        """
        ...

    def publish(self, stream_id: int, seq_no: int, priority: int, payload: bytes, flags: int = 0) -> bool:
        """Publishes a packet into the ring buffer with priority (0=Normal, 1=Medium, 2=High, 3=Critical). Returns True on success, False if dropped."""
        ...

    def poll_stream(self, stream_id: int) -> list[tuple[int, bytes]]:
        """Drains committed slots from the ring buffer for stream_id and returns strictly in-order, gapless (seq_no, payload) tuples."""
        ...

    def schedule_fiber(self, task_id: int, priority: int, work_fn: Callable[[], Any]):
        """Schedules a cooperative fiber task with priority (0-3). Higher priority fibers execute first with larger quantum ticks."""
        ...

    def step_fibers(self) -> int:
        """Steps and executes the highest-priority scheduled fiber. Returns executed priority, or -1 if idle."""
        ...

    def get_watermark_lag(self, stream_id: int) -> int:
        """Returns the watermark lag (high_watermark - low_watermark) for a given stream."""
        ...

    def step_clock(self, ticks: int = 1):
        """Advances the discrete-event logical clock by the specified number of ticks."""
        ...

    def get_telemetry(self) -> dict:
        """Returns telemetry statistics dictionary containing total_frames, dropped_frames, committed_bytes, p50_latency_ticks, p99_latency_ticks."""
        ...
```

---

## 2. Binary Wire Framing Specification

### Exact 20-Byte Header Layout (Network Big-Endian):
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       MAGIC (0x54585258)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     FLAGS     |    RESERVED   |           STREAM_ID           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                       SEQUENCE_NO (uint64)                    +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          PAYLOAD_LEN          |         HEADER_CRC16          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        PAYLOAD BYTES...                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      FRAME_CRC32 (uint32)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Protocol Fields & Integrity Ordering:
1. **`MAGIC` (uint32, 4 bytes):** Must equal `0x54585258` (`"TXRX"`).
2. **`FLAGS` (uint8, 1 byte):** Bitfield flags.
3. **`RESERVED` (uint8, 1 byte):** Must be `0x00`.
4. **`STREAM_ID` (uint16, 2 bytes):** Multi-stream identifier ($1 \le 	ext{stream\_id} \le 65535$).
5. **`SEQUENCE_NO` (uint64, 8 bytes):** Monotonic sequence counter.
6. **`PAYLOAD_LEN` (uint16, 2 bytes):** Length of payload bytes ($0 \le N \le 4096$).
7. **`HEADER_CRC16` (uint16, 2 bytes):** CRC-16 (Polynomial `0x1021`, initial `0xFFFF`) calculated strictly over header bytes `[0:18]`.
8. **`FRAME_CRC32` (uint32, 4 bytes):** CRC-32 (IEEE 802.3 standard) calculated strictly over the full frame prefix `[0:20+N]`.

### Integrity Ordering Principle (Crucial):
* **Integrity Validation First:** When decoding a raw byte stream, the **Header CRC-16 check MUST execute BEFORE field interpretation** (Magic / Reserved / Flags). A corrupted byte in the header region (even inside the Magic bytes) constitutes header bit rot and must raise `HeaderCorruptError`.
* If Header CRC-16 is valid but the Magic field does not match, raise `InvalidMagicError`.
* If Header CRC-16 is valid but Payload CRC-32 is corrupted, raise `PayloadCorruptError`.
* If `PAYLOAD_LEN` exceeds `4096`, raise `FrameOverflowError`.

---

## 3. Lock-Free MPMC Ring Buffer & Concurrency Subsystem

1. **Power-of-Two Masking:** Capacity $C$ must be a power of 2 ($M = C - 1$).
2. **Multi-Stream Linear Collision Probing:** Base slot is calculated as:
   $$	ext{base\_slot} = (	ext{stream\_id} 	imes 37 + 	ext{sequence\_no}) \ \& \ M$$
   If occupied, probe forward linearly up to $C$ steps.
3. **Turn-Based Lease Management & Epoch Tokens:**
   * Acquiring a slot allocates a lease stamped with `(lease_id, lease_epoch, expiry_tick)`.
   * Default lease duration is 10 logical ticks.
   * Committing requires validating that caller's `lease_id` and `lease_epoch` match the slot's current state.
4. **Strict Priority Preemption:**
   * When buffer is saturated, higher-priority streams ($	ext{priority} \in \{0, 1, 2, 3\}$) can only preempt **UNCOMMITTED** slot leases of lower priority.
   * **COMMITTED** unread data MUST NEVER be destroyed or overwritten by preemption.
5. **Backpressure Modes:**
   * `BLOCK`: Fails acquisition and returns `False` if no uncommitted slot can be allocated or preempted.
   * `DROP_OLDEST`: Evicts the slot with the lowest sequence number among committed slots.
   * `REJECT`: Immediately returns `False` without waiting.

---

## 4. Gapless Stream Reassembly Engine

1. **Dynamic Stream Initialization:**
   * A stream's initial expected sequence number is established dynamically by the **first received packet** for that `stream_id`. Streams do not necessarily start at 0.
2. **Strict In-Order Delivery:**
   * When `poll_stream(stream_id)` is invoked, the engine must deliver strictly contiguous packets starting from `expected_seq`.
   * If a gap is detected (e.g. sequence $K+2$ arrives while $K+1$ is missing), future packets must remain buffered in an out-of-order min-heap staging queue, and `poll_stream()` must return only packets up to the gap (or empty `[]` if the gap is at the head).
   * Once the missing packet $K+1$ arrives, both $K+1$ and all contiguous staged packets must be emitted.
3. **Modular uint64 Wraparound Arithmetic:**
   * Sequence distance calculations across the uint64 boundary ($2^{64}-1 	o 0$) must use directional modular arithmetic:
     $$\Delta = (	ext{seq\_no} - 	ext{expected\_seq}) \ \& \ ((1 \ll 64) - 1)$$
     If $\Delta == 0$: in-order packet. If $0 < \Delta < 2^{63}$: future packet. If $\Delta \ge 2^{63}$: stale/duplicate packet.

---

## 5. Cooperative Fiber Scheduler & Watermark Telemetry

1. **Priority Fiber Scheduling:**
   * `schedule_fiber(task_id, priority, work_fn)` stages callable tasks into priority queues (0 to 3).
   * `step_fibers()` pops and executes the highest-priority available task first (Priority 3 > 2 > 1 > 0) with quantum allocations. Returns executed priority or -1 if queues are empty.
2. **Stream Watermark Auditing:**
   * High-watermark tracks the highest committed sequence number per stream.
   * Low-watermark tracks the lowest unconsumed sequence number per stream.
   * `get_watermark_lag(stream_id)` computes $	ext{high\_watermark} - 	ext{low\_watermark}$.
3. **Discrete-Event Telemetry:**
   * `get_telemetry()` returns `total_frames`, `dropped_frames`, `committed_bytes`, `p50_latency_ticks`, `p99_latency_ticks`.

---

## 6. Evaluation & Rubric

* **Tier 1 (25%):** Binary wire framing, nested CRC-16/CRC-32 verification, integrity ordering.
* **Tier 2 (25%):** MPMC ring buffer, power-of-two linear probing, uint64 wraparound ($2^{64}-16 	o 0$).
* **Tier 3 (25%):** Gapless sliding window reassembly, dynamic stream initialization, telemetry percentiles.
* **Tier 4 (25%):** 2,400-state combinatorial stress matrix across 24 invariant topologies (including fiber priority dispatch and watermark lag).
