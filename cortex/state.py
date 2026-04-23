import json
import time
from pathlib import Path
from typing import Optional, Any


class AgentState:
    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.current_focus: Optional[str] = None
        self.error_streak: int = 0
        self.total_tokens_consumed: int = 0
        self.last_turn_timestamp: float = time.time()
        self._load_state()

    def _load_state(self):
        state_file = self.memory_dir / ".agent_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            self.current_focus = data.get("current_focus")
            self.error_streak = data.get("error_streak", 0)
            self.total_tokens_consumed = data.get("total_tokens_consumed", 0)
            self.last_turn_timestamp = data.get("last_turn_timestamp", time.time())

    def save(self):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "current_focus": self.current_focus,
            "error_streak": self.error_streak,
            "total_tokens_consumed": self.total_tokens_consumed,
            "last_turn_timestamp": self.last_turn_timestamp,
        }
        (self.memory_dir / ".agent_state.json").write_text(json.dumps(data))

    def set_focus(self, objective: str) -> Optional[str]:
        old = self.current_focus
        self.current_focus = objective
        self.save()
        return old

    def resolve_focus(self, synthesis: str) -> Optional[str]:
        old = self.current_focus
        self.current_focus = None
        self.save()
        return old
