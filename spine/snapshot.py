from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


class SnapshotManager:
    def __init__(self, snapshots_dir: str, interval: int):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.interval = interval

    def should_snapshot(self, turn_count: int) -> bool:
        return turn_count % self.interval == 0

    def save(self, snapshot: dict) -> None:
        snapshot["timestamp"] = datetime.now(timezone.utc).isoformat()
        path = self.snapshots_dir / "last_good_state.json"
        path.write_text(json.dumps(snapshot, indent=2))

    def load(self) -> dict | None:
        path = self.snapshots_dir / "last_good_state.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return data
