"""Stream Sequence & State Tracker."""

class StreamTracker:
    def __init__(self, stream_id: int, initial_seq: int = 0):
        self.stream_id = stream_id
        self.expected_seq = initial_seq
        self.highest_seen_seq = initial_seq
        self.delivered_count = 0
        self.is_initialized = False

    def initialize_if_new(self, first_seq: int):
        if not self.is_initialized:
            self.expected_seq = first_seq
            self.highest_seen_seq = first_seq
            self.is_initialized = True

    def advance_expected(self, next_seq: int):
        self.expected_seq = next_seq
        self.delivered_count += 1
