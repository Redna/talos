from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


class EventLogger:
    def __init__(self, events_dir: str):
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self._file = None
        self._current_date: str = ""

    def _ensure_file(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._file:
                self._file.close()
            path = self.events_dir / f"{today}.jsonl"
            self._file = open(path, "a", encoding="utf-8")
            self._current_date = today

    def emit(self, event_type: str, payload: dict[str, object]):
        self._ensure_file()
        event = {"type": event_type, "ts": datetime.now(timezone.utc).isoformat()}
        event.update(payload)
        self._file.write(json.dumps(event) + "\n")
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
            self._file = None
            self._current_date = ""

    def recent_events(self, n: int = 100) -> list[dict]:
        """Read the last n events from the event log, newest last."""
        events_dir = Path(self.events_dir)
        all_events = []
        for jsonl_file in sorted(events_dir.glob("*.jsonl")):
            try:
                for line in jsonl_file.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        all_events.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
            except FileNotFoundError:
                continue
        return all_events[-n:]
