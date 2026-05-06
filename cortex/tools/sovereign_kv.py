import json
import os
from typing import Any, Dict, Optional

class SovereignKV:
    """
    A simple persistent key-value store for the agent's cognitive state.
    Supports persistent storage and named checkpoints for state restoration.
    """
    def __init__(self, storage_path: str = "/memory/sovereign_kv.json", checkpoints_dir: str = "/memory/checkpoints"):
        self.storage_path = storage_path
        self.checkpoints_dir = checkpoints_dir
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"[ERROR] Failed to save KV store: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self._save()

    def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            self._save()

    def keys(self) -> list:
        return list(self.data.keys())

    def checkpoint(self, name: str):
        """Saves the current state as a named checkpoint."""
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        checkpoint_path = os.path.join(self.checkpoints_dir, f"{name}.json")
        try:
            with open(checkpoint_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            return f"Checkpoint '{name}' saved successfully."
        except IOError as e:
            return f"Failed to save checkpoint: {e}"

    def restore_checkpoint(self, name: str):
        """Restores the state from a named checkpoint."""
        checkpoint_path = os.path.join(self.checkpoints_dir, f"{name}.json")
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r') as f:
                self.data = json.load(f)
            self._save()
            return f"Checkpoint '{name}' restored successfully."
        return f"Checkpoint '{name}' not found."

# Global instance for easy access
kv = SovereignKV()
