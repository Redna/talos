import json
import os
from pathlib import Path
from typing import Any, Dict, List

STATE_FILE = "/memory/operational/sovereign_state.json"

class SovereignState:
    """
    SovereignState: Managed access to the sovereign state file.
    Handles the persistence of evolutionary progress and cognitive status.
    """
    def __init__(self):
        self.path = Path(STATE_FILE)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"identity": {}, "evolutionary_progress": {"resolved_objectives": [], "pending_tasks": []}}
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, IOError):
            return {"identity": {}, "evolutionary_progress": {"resolved_objectives": [], "pending_tasks": []}}

    def save(self, state: Dict[str, Any]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, indent=2))

    def add_resolved_objective(self, objective: str):
        """Adds a unique objective to the resolved list."""
        state = self.load()
        resolved = state.get("evolutionary_progress", {}).get("resolved_objectives", [])
        
        # We identify the base capability name from the objective string
        # e.g., "S-Pattern-Matcher: Implement..." -> "S-Pattern-Matcher"
        capability = objective.split(":")[0].strip()
        
        if capability not in resolved:
            resolved.append(capability)
            state["evolutionary_progress"]["resolved_objectives"] = resolved
            self.save(state)
        return capability

    def remove_pending_task(self, task_text: str):
        """Removes a task from the pending list."""
        state = self.load()
        pending = state.get("evolutionary_progress", {}).get("pending_tasks", [])
        # Remove task if it matches exactly or starts with the objective
        pending = [t for t in pending if t != task_text]
        state["evolutionary_progress"]["pending_tasks"] = pending
        self.save(state)
