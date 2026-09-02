"""Deterministic Discrete-Event Virtual Clock."""

class VirtualClock:
    def __init__(self, start_tick: int = 0):
        self._current_tick = start_tick

    @property
    def current_tick(self) -> int:
        return self._current_tick

    def tick(self, delta: int = 1) -> int:
        if delta < 0:
            raise ValueError(f"Clock tick delta cannot be negative: {delta}")
        self._current_tick += delta
        return self._current_tick

    def reset(self, tick: int = 0):
        self._current_tick = tick
