"""Sanity Verification Test Suite (Single-Stream Baseline)."""
import pytest

def test_sanity_single_stream_basic():
    """Validates basic single-stream sequential publish and drain."""
    from engine.transceiver import Transceiver
    tx = Transceiver(capacity=64)
    # Simple single-stream monotonic sequence
    assert tx.publish(stream_id=1, seq_no=0, priority=0, payload=b"sample_data") is True
    res = tx.poll_stream(1)
    assert len(res) == 1
    assert res[0] == (0, b"sample_data")
