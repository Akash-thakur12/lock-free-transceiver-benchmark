"""Lock-Free Transaction Logger."""

class TransactionLogger:
    def __init__(self):
        self.total_frames = 0
        self.dropped_frames = 0
        self.committed_bytes = 0
        self.preempted_leases = 0

    def log_commit(self, byte_count: int):
        self.total_frames += 1
        self.committed_bytes += byte_count

    def log_drop(self):
        self.total_frames += 1
        self.dropped_frames += 1

    def log_preempt(self):
        self.preempted_leases += 1
