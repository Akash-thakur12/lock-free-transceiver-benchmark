# Task: High-Throughput Lock-Free Ring Buffer & Zero-Copy Transceiver

## Overview
Implement a high-performance, discrete-event packet transceiver engine in Python (`engine/`). The system manages multi-stream binary packet encoding/decoding, lock-free ring buffering with priority preemption, gapless out-of-order reassembly, and microsecond-level telemetry.

---

## 1. Binary Wire Framing Specification

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

### Protocol Fields & Validation Rules:
1. **`MAGIC` (uint32, 4 bytes):** Must equal `0x54585258` (`"TXRX"`).
2. **`FLAGS` (uint8, 1 byte):** Bitfield flags.
3. **`RESERVED` (uint8, 1 byte):** Must be `0x00`.
4. **`STREAM_ID` (uint16, 2 bytes):** Multi-stream identifier ($1 \le 	ext{stream\_id} \le 65535$).
5. **`SEQUENCE_NO` (uint64, 8 bytes):** Monotonic sequence counter. Streams may begin at any arbitrary `uint64` start value.
6. **`PAYLOAD_LEN` (uint16, 2 bytes):** Length of payload bytes ($0 \le N \le 4096$).
7. **`HEADER_CRC16` (uint16, 2 bytes):** CRC-16 (Polynomial `0x1021`, initial `0xFFFF`) calculated strictly over header bytes `[0:18]`.
8. **`FRAME_CRC32` (uint32, 4 bytes):** CRC-32 (IEEE 802.3 standard) calculated strictly over the full frame prefix `[0:20+N]`.

### Integrity Ordering Principle (Crucial):
* **Integrity Validation First:** When decoding a raw byte stream, the **Header CRC-16 check MUST execute BEFORE field interpretation** (such as Magic, Reserved, or Flags). A corrupted byte in the header region (even inside the Magic bytes) constitutes header bit rot and must raise `HeaderCorruptError`.
* If Header CRC-16 is valid but the Magic field does not match, raise `InvalidMagicError`.
* If Header CRC-16 is valid but Payload CRC-32 is corrupted, raise `PayloadCorruptError`.
* If `PAYLOAD_LEN` exceeds `4096`, raise `FrameOverflowError`.

---

## 2. Lock-Free MPMC Ring Buffer & Concurrency Subsystem

1. **Power-of-Two Masking:** Capacity $C$ must be a power of 2 ($M = C - 1$).
2. **Multi-Stream Linear Collision Probing:** Base slot is calculated as:
   $$	ext{base\_slot} = (	ext{stream\_id} 	imes 37 + 	ext{sequence\_no}) \ \& \ M$$
   If the slot is occupied, probe forward linearly up to $C$ steps.
3. **Turn-Based Lease Management & Epoch Tokens:**
   * Acquiring a slot allocates a lease stamped with `(lease_id, lease_epoch, expiry_tick)`.
   * Default lease duration is 10 logical ticks.
   * Committing requires validating that the caller's `lease_id` and `lease_epoch` match the slot's current state.
4. **Strict Priority Preemption:**
   * When the buffer is saturated, higher-priority streams ($	ext{priority} \in \{0, 1, 2, 3\}$) can only preempt **UNCOMMITTED** slot leases of lower priority.
   * **COMMITTED** unread data MUST NEVER be destroyed or overwritten by preemption.
5. **Backpressure Modes:**
   * `BLOCK`: Fails acquisition and returns `False` if no uncommitted slot can be allocated or preempted.
   * `DROP_OLDEST`: Evicts the slot with the lowest sequence number among committed slots.
   * `REJECT`: Immediately returns `False` without waiting.

---

## 3. Gapless Stream Reassembly Engine

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

## 4. Discrete-Event Scheduler & Telemetry

1. **Deterministic Virtual Clock:** Discrete tick progression via `step_clock(ticks)`.
2. **Histogram & Percentiles:** Calculate p50 and p99 transaction latencies in logical ticks.
3. **Telemetry Exporter:** `get_telemetry()` returns `total_frames`, `dropped_frames`, `committed_bytes`, `p50_latency_ticks`, `p99_latency_ticks`.

---

## 5. Evaluation & Rubric

* **Tier 1 (25%):** Binary wire framing, nested CRC-16/CRC-32 verification, integrity ordering.
* **Tier 2 (25%):** MPMC ring buffer, power-of-two linear probing, uint64 wraparound ($2^{64}-16 	o 0$).
* **Tier 3 (25%):** Gapless sliding window reassembly, dynamic stream initialization, telemetry percentiles.
* **Tier 4 (25%):** 1,600-state combinatorial stress matrix across 16 invariant topologies.
