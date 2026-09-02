"""Worker Execution Context & State Machine."""
from enum import Enum

class WorkerState(Enum):
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    TERMINATED = 4

class WorkerContext:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.state = WorkerState.READY
        self.current_lease_id = -1
        self.yield_count = 0

    def block_on_buffer(self):
        self.state = WorkerState.BLOCKED
        self.yield_count += 1

    def unblock(self):
        self.state = WorkerState.READY
