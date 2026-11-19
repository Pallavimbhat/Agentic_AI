"""Append-only JSONL execution logger for Lab 6 demonstrations."""
import json
from pathlib import Path
from datetime import datetime, timezone

class ExecutionLogger:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(__file__).parent / "data" / "audit_log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read(self, limit=50):
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-max(1, min(int(limit), 500)):]
