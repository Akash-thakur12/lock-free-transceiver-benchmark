# Discrete-Event Lock-Free Ring Buffer & Zero-Copy Framing Transceiver Benchmark

## Objective
Implement a high-performance, deterministic **Discrete-Event Lock-Free Ring Buffer & Zero-Copy Framing Transceiver Engine** supporting nested CRC binary framing, turn-based MPMC slot leasing, priority lease preemption, gapless sliding-window reassembly, and lock-free telemetry logging across a **1,600-state combinatorial stress matrix**.

---

## Technical Specifications & Wire Protocol

### 1. 20-Byte Big-Endian Header & Frame Layout
Every transmitted frame consists of a 20-byte header, an $N$-byte payload ($0 \le N \le 4096$), and a 4-byte trailing Frame CRC-32:

| Field Name | Offset | Length | Type | Description |
|:---|:---:|:---:|:---:|:---|
| **`MAGIC`** | `0x00` | 4 Bytes | `uint32` | Must equal `0x54585258` (`"TXRX"` in ASCII). |
| **`flags`** | `0x04` | 1 Byte | `uint8` | Bitmask: `0x01`=SYN, `0x02`=FIN, `0x04`=URG, `0x08`=COMPRESSED. |
| **`reserved`** | `0x05` | 1 Byte | `uint8` | Reserved byte (must be `0x00`). |
| **`stream_id`**| `0x06` | 2 Bytes | `uint16` | Logical Stream Identifier (`0` to `65535`). |
| **`sequence_no`**| `0x08` | 8 Bytes | `uint64` | Monotonic Big-Endian Sequence Number. |
| **`payload_len`**| `0x10` | 2 Bytes | `uint16` | Payload length in bytes ($0 \le N \le 4096$). |
| **`header_crc`**| `0x12` | 2 Bytes | `uint16` | CRC-16 (Poly `0x1021`, Init `0xFFFF`) over header bytes `[0:18]`. |

$$\text{Wire Frame} = \underbrace{\text{Header (20B)}}_{[0:20]} + \underbrace{\text{Payload (N Bytes)}}_{[20:20+N]} + \underbrace{\text{Frame CRC-32 (4B)}}_{[20+N:24+N]}$$

* **Header CRC-16:** Computed strictly over the first 18 bytes (`[0:18]`). If corrupted, the decoder MUST raise `HeaderCorruptError` without processing payload.
* **Frame CRC-32:** Computed strictly over `[0 : 20 + payload_len]` (Header + Payload combined, excluding the trailing 4-byte CRC-32). If corrupted, the decoder MUST raise `PayloadCorruptError`.
* If `MAGIC != 0x54585258` or `reserved != 0x00`, the decoder MUST raise `InvalidMagicError`.
* If `payload_len > 4096`, the decoder MUST raise `FrameOverflowError`.

---

## 2. Lock-Free MPMC Ring Buffer Architecture

The ring buffer operates on a fixed power-of-two capacity $C = 2^k$ (mask $M = C - 1$):
* **Turn-Based Sequence Indexing:**
  $$\text{slot\_idx} = \text{sequence\_no} \ \& \ M$$
  Each slot tracks: `sequence_no`, `producer_turn`, `consumer_turn`, `priority` (0=Normal, 1=Medium, 2=High, 3=Critical), and `lease_expiry_tick`.
* **Zero-Copy Slot Lease & Commit:**
  * `acquire_lease(stream_id, priority, size) -> (lease_id, slot_idx)`
  * `commit_lease(lease_id, data: bytes)`
* **Priority Lease Preemption:**
  * When buffer capacity is fully occupied, a new request with `priority >= 2` can preempt an expired or lower-priority uncommitted lease.
* **Sequence Wraparound Invariant:**
  * When `sequence_no` wraps from $2^{64}-1$ to $0$, slot indexing and turn arithmetic MUST continue seamlessly without deadlocks or buffer corruption.

---

## 3. Gapless Sliding Reassembly Window

* Multi-producer out-of-order commits are ingested into a stream reassembly table.
* The consumer MUST deliver strictly **gapless contiguous sequence numbers** per `stream_id`. If sequence $K+1$ arrives before $K$, it must buffer $K+1$ until $K$ is committed.

---

## 4. Deterministic Discrete-Event Virtual Clock

* All concurrency is evaluated through a deterministic `VirtualClock`:
  * `clock.tick(delta=1)` advances discrete logical time.
  * Backpressure policies: `BLOCK` (yields until slot freed), `DROP_OLDEST` (drops lowest-turn unconsumed slot), `REJECT` (raises `BufferOverflowError`).
* `get_telemetry()` returns `{total_frames, dropped_frames, committed_bytes, p50_latency_ticks, p99_latency_ticks}`.

---

## Public API Contract

Candidate implementations under `engine.transceiver` must expose:

### `Transceiver(capacity: int = 128, backpressure: str = "BLOCK")`
* `encode_frame(stream_id: int, seq_no: int, flags: int, payload: bytes) -> bytes`
* `decode_frame(frame_bytes: bytes) -> tuple[dict, bytes]`
* `publish(stream_id: int, seq_no: int, priority: int, payload: bytes) -> bool`
* `poll_stream(stream_id: int) -> list[tuple[int, bytes]]` (Returns contiguous committed `(seq_no, payload)`)
* `step_clock(ticks: int = 1)`
* `get_telemetry() -> dict`

### Exception Hierarchy (`engine.codec`):
* `TransceiverError(Exception)`
* `InvalidMagicError(TransceiverError)`
* `HeaderCorruptError(TransceiverError)`
* `PayloadCorruptError(TransceiverError)`
* `FrameOverflowError(TransceiverError)`
* `BufferOverflowError(TransceiverError)`
* `SlotStateViolationError(TransceiverError)`

---

## Grading & Partial Credit Rubric

The evaluation suite (`tests/test_outputs.py`) executes a 4-tier grading pipeline:

| Tier | Component | Weight | Criteria |
|:---|:---|:---:|:---|
| **Tier 1** | **Wire Framing & Nested CRC Safety** | `0.250` | 20B Header, CRC-16 [0:18], CRC-32 [0:20+N], Magic & boundary traps. |
| **Tier 2** | **Lock-Free MPMC Ring Buffer** | `0.250` | Turn-based indexing, zero-copy slot leasing, uint64 wraparound ($2^{64}-16 \to 0$). |
| **Tier 3** | **Reassembly, Preemption & Telemetry** | `0.250` | Gapless sliding window, priority preemption, and p50/p99 latency tracking. |
| **Tier 4** | **1,600-State Combinatorial Matrix** | `0.250` | 16 distinct operational & fault scenarios $\times 100$ variations (1,600 states). |

* **Total Score:** $\sum \text{Tiers} = \mathbf{1.0000}$
* **Passing Threshold:** $\text{Score} \ge \mathbf{0.5000}$
