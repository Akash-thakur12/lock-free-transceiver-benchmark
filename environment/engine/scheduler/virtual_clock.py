"""Virtual Clock Starter Scaffold."""

class VirtualClock:
    def __init__(self, start_tick: int = 0):
        self._current_tick = start_tick

    @property
    def current_tick(self) -> int:
        return self._current_tick

    def tick(self, delta: int = 1) -> int:
        return 0
