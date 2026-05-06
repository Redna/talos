import json
import os
from typing import Any, Dict, Optional

class SovereignKV:
    """
    A simple persistent key-value store for the agent's cognitive state.
    Stored as a JSON file in the agent's memory.
    """
    def __init__(self, storage_path: str = "/memory/sovereign_kv.json"):
        self.storage_path = storage_path
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

# Global instance for easy access
kv = SovereignKV()
