import json
import subprocess
import os
from typing import Dict, Any

class SovereignStateSnapshot:
    """
    Composite Operator: Sovereign State Snapshot.
    Collapses multiple system probes into a single high-density report.
    Reduces metabolic noise for the LLM.
    """
    def __init__(self):
        self.paths = {
            "handover": "/memory/signals/handover_state.json",
            "parity": "/memory/signals/parity_state.json",
            "world": "/memory/world_external.md"
        }

    def _read_json(self, path: str) -> Any:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            return {"error": str(e)}
        return None

    def _read_file_tail(self, path: str, lines: int = 5) -> str:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return "".join(f.readlines()[-lines:])
        except Exception as e:
            return f"Error reading file: {str(e)}"
        return "File not found"

    def capture(self) -> Dict[str, Any]:
        snapshot = {
            "handover": self._read_json(self.paths["handover"]),
            "parity": self._read_json(self.paths["parity"]),
            "world_latest": self._read_file_tail(self.paths["world"]),
            "git_status": self._get_git_status(),
            "cortex_health": self._get_cortex_health()
        }
        return snapshot

    def _get_git_status(self) -> str:
        try:
            return subprocess.check_output(["git", "status", "--short"], text=True)
        except Exception as e:
            return str(e)

    def _get_cortex_health(self) -> Dict[str, Any]:
        try:
            distilled_path = "/app/cortex/distilled/"
            count = len(os.listdir(distilled_path)) if os.path.exists(distilled_path) else 0
            return {"distilled_primitives": count, "status": "NOMINAL"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    snapshot_engine = SovereignStateSnapshot()
    print(json.dumps(snapshot_engine.capture(), indent=2))
