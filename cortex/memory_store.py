"""
Memory Store — Key-value store operations on /memory/.
"""
import json
from pathlib import Path
from typing import Optional


MAX_MEMORY_SLOTS = 50


"""
Memory Store — Key-value store operations on /memory/ with cognitive metadata.
"""
import json
import time
from pathlib import Path
from typing import Optional, Any


MAX_MEMORY_SLOTS = 50


class MemoryStore:
    """Key-value store backed by agent_memory.json in /memory/ with temporal tracking."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.store_file = memory_dir / "agent_memory.json"
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.store_file.exists():
            try:
                loaded = json.loads(self.store_file.read_text())
                # Migration: Convert old flat dict[str, str] to dict[str, dict]
                if loaded:
                    first_val = next(iter(loaded.values()))
                    if isinstance(first_val, str):
                        self._data = {
                            k: {
                                "value": v,
                                "created_at": time.time(),
                                "last_accessed_at": time.time(),
                                "access_count": 0,
                            }
                            for k, v in loaded.items()
                        }
                    else:
                        self._data = loaded
                else:
                    self._data = {}
            except (json.JSONDecodeError, KeyError):
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        self.store_file.write_text(json.dumps(self._data, indent=2))

    def store(self, key: str, value: str) -> str:
        """Store a key-value pair with initialization metadata."""
        if len(key) > 100:
            return f"[ERROR] Key too long (max 100 chars): {key[:50]}..."
        
        now = time.time()
        is_new = key not in self._data
        
        if is_new and len(self._data) >= MAX_MEMORY_SLOTS:
            return f"[ERROR] Memory full ({MAX_MEMORY_SLOTS} slots). Use forget_memory to free slots."
        
        if is_new:
            self._data[key] = {
                "value": value,
                "created_at": now,
                "last_accessed_at": now,
                "access_count": 0,
            }
        else:
            # Update existing value, preserve creation date
            self._data[key]["value"] = value
            self._data[key]["last_accessed_at"] = now
            self._data[key]["access_count"] += 1
            
        self._save()
        return f"[STORED] {key}"

    def recall(self, key: str) -> str:
        """Retrieve value and update access telemetry."""
        now = time.time()
        target_key = None
        
        if key in self._data:
            target_key = key
        else:
            # Partial match
            for k in self._data:
                if key.lower() in k.lower():
                    target_key = k
                    break
        
        if target_key:
            self._data[target_key]["last_accessed_at"] = now
            self._data[target_key]["access_count"] += 1
            self._save()
            return self._data[target_key]["value"]
            
        return f"[NOT FOUND] No memory matching '{key}'"

    def forget(self, key: str) -> str:
        """Delete a memory entry."""
        if key in self._data:
            del self._data[key]
            self._save()
            return f"[FORGOTTEN] {key}"
        return f"[NOT FOUND] No memory matching '{key}'"

    def list_keys(self) -> list[str]:
        """Return all memory keys."""
        return list(self._data.keys())

    def get_metadata(self, key: str) -> Optional[dict[str, Any]]:
        """Retrieve telemetry for a specific memory."""
        if key in self._data:
            return {k: v for k, v in self._data[key].items() if k != "value"}
        return None

    def list_all_metadata(self) -> dict[str, dict[str, Any]]:
        """Return metadata for all memories for synthesis review."""
        return {
            k: {pk: pv for pk, pv in v.items() if pk != "value"}
            for k, v in self._data.items()
        }

    @property
    def count(self) -> int:
        return len(self._data)
