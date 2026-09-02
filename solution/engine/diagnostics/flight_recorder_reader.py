"""High-Speed Telemetry Flight Recorder Parser."""
import json
from pathlib import Path

class FlightRecorderReader:
    """Parses JSON-lines telemetry flight recorder traces."""
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)

    def scan_violations(self, max_records: int = 5000) -> list[dict]:
        violations = []
        if not self.log_path.exists():
            return violations

        with open(self.log_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if count >= max_records:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("status") == "PREEMPTED" or record.get("latency_ticks", 0) > 20:
                        violations.append(record)
                    count += 1
                except Exception:
                    pass
        return violations
