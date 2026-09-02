"""Priority Event Queue for Scheduled Logical Ticks."""
import heapq

class EventQueue:
    def __init__(self):
        self._events: list[tuple[int, int, str, dict]] = []  # (scheduled_tick, priority, event_type, data)
        self._seq = 0

    def schedule_event(self, tick: int, priority: int, event_type: str, data: dict = None):
        heapq.heappush(self._events, (tick, priority, self._seq, event_type, data or {}))
        self._seq += 1

    def pop_ready_events(self, current_tick: int) -> list[tuple[str, dict]]:
        ready = []
        while self._events and self._events[0][0] <= current_tick:
            _, _, _, event_type, data = heapq.heappop(self._events)
            ready.append((event_type, data))
        return ready

    def is_empty(self) -> bool:
        return len(self._events) == 0
