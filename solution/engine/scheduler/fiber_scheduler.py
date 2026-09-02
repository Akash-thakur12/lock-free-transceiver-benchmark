"""Cooperative Fiber Scheduler with Priority Quantum Allocation."""
from collections import deque
from typing import Callable, Any

class FiberTask:
    def __init__(self, task_id: int, priority: int, work_fn: Callable[[], Any], quantum_ticks: int):
        self.task_id = task_id
        self.priority = priority
        self.work_fn = work_fn
        self.quantum_ticks = quantum_ticks
        self.remaining_ticks = quantum_ticks
        self.is_completed = False
        self.result = None

class CooperativeFiberScheduler:
    def __init__(self):
        self.queues: dict[int, deque[FiberTask]] = {0: deque(), 1: deque(), 2: deque(), 3: deque()}
        self.total_scheduled = 0
        self.total_completed = 0

    def spawn(self, task_id: int, priority: int, work_fn: Callable[[], Any]):
        priority = max(0, min(3, priority))
        # Quantum allocation: Priority 0 -> 1 tick, Priority 1 -> 2 ticks, Priority 2 -> 3 ticks, Priority 3 -> 4 ticks
        quantum = priority + 1
        task = FiberTask(task_id, priority, work_fn, quantum)
        self.queues[priority].append(task)
        self.total_scheduled += 1

    def step(self) -> int:
        """Executes the highest priority available fiber task. Returns executed priority, or -1 if idle."""
        for p in (3, 2, 1, 0):
            if self.queues[p]:
                task = self.queues[p].popleft()
                try:
                    task.result = task.work_fn()
                    task.is_completed = True
                    self.total_completed += 1
                except Exception as e:
                    task.result = e
                    task.is_completed = True
                return p
        return -1
