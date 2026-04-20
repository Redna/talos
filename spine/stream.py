from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from spine.config import SpineConfig
from spine.constitution import load_system_prompt

STALL_WINDOW = 10
STALL_THRESHOLD = 5


class StreamManager:
    def __init__(self, cfg: SpineConfig):
        self.cfg = cfg
        self._messages: list[dict[str, Any]] = []
        self.turn = 0
        self._system_prompt = load_system_prompt(
            cfg.constitution_path, cfg.identity_path
        )
        self._stall_notices_sent = 0
        self.queued_notices: list[str] = []
        self._init_messages()

    def _init_messages(self):
        self._messages = [{"role": "system", "content": self._system_prompt}]

    @property
    def messages(self) -> list[dict[str, Any]]:
        return self._messages

    def add_message(self, msg: dict):
        self._messages.append(msg)

    def record_tool_result(self, tool_call_id: str, output: str, success: bool):
        self.add_message(
            {"role": "tool", "tool_call_id": tool_call_id, "content": output}
        )

    def piggyback_hud(self, hud_data: dict[str, Any]):
        hud_line = (
            f"\n[HUD] turn={hud_data.get('turn', 0)}"
            f" context_pct={hud_data.get('context_pct', 0.0):.2f}"
            f" urgency={hud_data.get('urgency', 'nominal')}"
            f" memory_files={hud_data.get('memory_files', 0)}"
            f" focus={hud_data.get('focus', '')}"
        )
        for msg in reversed(self._messages):
            if msg.get("role") == "tool":
                msg["content"] += hud_line
                return
        self.add_message({"role": "user", "content": hud_line.strip()})

    def fold(self, synthesis: str):
        traj_dir = Path(self.cfg.spine_dir) / "trajectories"
        traj_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        traj_path = traj_dir / f"{ts}.json"
        traj_path.write_text(json.dumps(self._messages, indent=2))
        self._init_messages()
        self.add_message({"role": "assistant", "content": synthesis})
        self.turn = 0

    def detect_stall(self) -> bool:
        assistant_msgs = [m for m in self._messages if m.get("role") == "assistant"]
        window = assistant_msgs[-STALL_WINDOW:]
        counts: Counter[str] = Counter()
        for msg in window:
            for tc in msg.get("tool_calls", []):
                func = (
                    tc.get("function")
                    if isinstance(tc, dict)
                    else getattr(tc, "function", None)
                )
                if func is None:
                    continue
                name = (
                    func.get("name")
                    if isinstance(func, dict)
                    else getattr(func, "name", None)
                )
                if name:
                    counts[name] += 1
        stalled = False
        for tool_name, count in counts.items():
            if count >= STALL_THRESHOLD:
                stalled = True
                self._stall_notices_sent += 1
                self.queue_system_notice(
                    f"STALL DETECTED: tool '{tool_name}' called {count} times in last {STALL_WINDOW} assistant turns"
                )
                if self._stall_notices_sent >= 3:
                    self.queue_system_notice(
                        f"CRITICAL: Stall detected {self._stall_notices_sent} times. Agent may be stuck in a loop."
                    )
                break
        if not stalled:
            self._stall_notices_sent = 0
        return stalled

    def queue_system_notice(self, text: str):
        self.queued_notices.append(text)

    def build_payload(self, tools: list[dict], hud_data: dict[str, Any]) -> list[dict]:
        payload = list(self._messages)
        if self.queued_notices:
            notice_text = "\n".join(self.queued_notices)
            payload.append({"role": "user", "content": notice_text})
            self.queued_notices.clear()
        return payload

    def write_state(
        self, focus: str = "", context_pct: float = 0.0, urgency: str = "nominal"
    ):
        mem_dir = Path(self.cfg.memory_dir)
        md_files = sorted(mem_dir.glob("*.md"))
        last_files = [f.name for f in md_files[-10:]]
        state = {
            "turn": self.turn,
            "context_pct": context_pct,
            "focus": focus,
            "urgency": urgency,
            "memory_file_count": len(md_files),
            "last_files": last_files,
        }
        state_path = Path(self.cfg.spine_dir) / "state.json"
        state_path.write_text(json.dumps(state, indent=2))
