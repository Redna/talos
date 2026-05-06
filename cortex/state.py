import json
from pathlib import Path
from typing import Optional


class AgentState:
    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.current_focus: Optional[str] = None
        self.error_streak: int = 0
        self.total_tokens_consumed: int = 0
        self.turns_since_pulse: int = 0
        self.design_turns: int = 0
        self._load_state()

    def _load_state(self):
        state_file = self.memory_dir / ".agent_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            self.current_focus = data.get("current_focus")
            self.error_streak = data.get("error_streak", 0)
            self.total_tokens_consumed = data.get("total_tokens_consumed", 0)
            self.turns_since_pulse = data.get("turns_since_pulse", 0)
            self.design_turns = data.get("design_turns", 0)

    def save(self):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "current_focus": self.current_focus,
            "error_streak": self.error_streak,
            "total_tokens_consumed": self.total_tokens_consumed,
            "turns_since_pulse": self.turns_since_pulse,
            "design_turns": self.design_turns,
        }
        (self.memory_dir / ".agent_state.json").write_text(json.dumps(data))

    def set_focus(self, objective: str) -> Optional[str]:
        old = self.current_focus
        self.current_focus = objective
        self.turns_since_pulse = 0
        self.save()
        return old

    def resolve_focus(self, synthesis: str) -> Optional[str]:
        old = self.current_focus
        self.current_focus = None
        self.save()
        return old
