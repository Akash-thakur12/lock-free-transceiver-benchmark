"""Deterministic Discrete-Event Virtual Clock."""

class VirtualClock:
    def __init__(self):
        self.current_tick = 0

    def tick(self, delta: int = 1) -> int:
        self.current_tick += delta
        return self.current_tick
