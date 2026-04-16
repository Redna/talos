from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


class SnapshotManager:
    def __init__(self, snapshots_dir: str, interval: int, memory_dir: str = None):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.interval = interval
        self.memory_dir = Path(memory_dir) if memory_dir else None

    def should_snapshot(self, turn_count: int) -> bool:
        return turn_count % self.interval == 0

    def save(self, snapshot: dict) -> None:
        snapshot_path = self.snapshots_dir / "last_good_state.json"
        
        # Merge current cognitive state (.agent_state.json) into the snapshot
        # to ensure focus and error streaks are preserved across recovery.
        if self.memory_dir:
            agent_state_file = self.memory_dir / ".agent_state.json"
            if agent_state_file.exists():
                try:
                    agent_data = json.loads(agent_state_file.read_text())
                    snapshot["agent_state"] = agent_data
                except Exception as e:
                    import logging
                    logging.getLogger("spine.snapshot").warning(f"Could not merge agent_state into snapshot: {e}")

        with open(snapshot_path, "w") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": snapshot
            }, f, indent=2)

    def load(self) -> dict | None:
        snapshot_path = self.snapshots_dir / "last_good_state.json"
        if not snapshot_path.exists():
            return None
        try:
            with open(snapshot_path, "r") as f:
                return json.load(f).get("data")
        except Exception:
            return None

    def restore(self, memory_dir: str) -> bool:
        """
        Restores the memory state from the last good snapshot.
        Returns True if restoration was successful.
        """
        data = self.load()
        if data is None:
            return False
        
        mem_path = Path(memory_dir)
        try:
            mem_path.mkdir(parents=True, exist_ok=True)
            
            # Restore primary state file (the backbone)
            state_file = mem_path / "state.json"
            state_file.write_text(json.dumps(data, indent=2))
            
            # Restore agent-specific state (focus, etc)
            agent_state = data.get("agent_state")
            if agent_state:
                agent_state_file = mem_path / ".agent_state.json"
                agent_state_file.write_text(json.dumps(agent_state, indent=2))
                
            return True
        except Exception as e:
            import logging
            logging.getLogger("spine.snapshot").error(f"Failed to restore memory: {e}")
            return False