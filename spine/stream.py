from __future__ import annotations

import copy
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
        state_path = Path(cfg.spine_dir) / "state.json"
        if state_path.exists():
            try:
                saved = json.loads(state_path.read_text())
                self.turn = saved.get("turn", 0)
            except Exception:
                self.turn = 0
        else:
            self.turn = 0
        self._system_prompt = load_system_prompt(
            cfg.constitution_path, cfg.identity_path
        )
        self._stall_notices_sent = 0
        self._hud_data: dict[str, Any] | None = None
        self._queued_notices: list[str] = []
        self._user_messages: list[str] = []
        self._hud_piggybacked = False
        # Index of the last message that received a HUD suffix. Ensures each
        # message is only ever decorated once, keeping the stream immutable.
        self._hud_last_index = -1
        self._init_messages()

    def _init_messages(self):
        self._messages = [{"role": "system", "content": self._system_prompt}]

    @property
    def messages(self) -> list[dict[str, Any]]:
        return self._messages

    @property
    def queued_notices(self) -> list[str]:
        return self._queued_notices

    def add_message(self, msg: dict):
        self._messages.append(dict(msg))
        self._hud_piggybacked = False

    def record_tool_result(self, tool_call_id: str, output: str, success: bool):
        self.add_message(
            {"role": "tool", "tool_call_id": tool_call_id, "content": output}
        )

    def set_hud(self, hud_data: dict[str, Any]):
        self._hud_data = dict(hud_data)
        self._hud_piggybacked = False

    def _build_hud_message(self) -> dict:
        """Build a minimal HUD user message for post-fold stream anchoring."""
        mem_dir = Path(self.cfg.memory_dir)
        md_files = sorted(mem_dir.glob("*.md")) if mem_dir.exists() else []
        return {
            "role": "user",
            "content": (
                f"[HUD] turn=0 context_pct=0.00 urgency=nominal "
                f"memory_files={len(md_files)} focus=none"
            ),
        }

    def _fold_metadata(self, msg_count: int) -> str:
        """Build a metadata line describing what was folded."""
        total_chars = sum(
            len(json.dumps(m, ensure_ascii=False)) for m in self._messages
        )
        approx_tokens = max(1, int(total_chars / 3.5))
        return (
            f"[METADATA] {msg_count} messages archived, "
            f"~{approx_tokens} tokens, ~{total_chars} chars"
        )

    def fold(self, synthesis: str, is_cortex_initiated: bool = False):
        msg_count = len(self._messages)
        metadata = self._fold_metadata(msg_count)

        # Capture last assistant + tool messages before archiving
        preserved_assistant = None
        preserved_tool = None
        if is_cortex_initiated and msg_count >= 2:
            last = self._messages[-1]
            second_last = self._messages[-2]
            if second_last.get("role") == "assistant" and last.get("role") == "tool":
                preserved_assistant = dict(second_last)
                preserved_tool = dict(last)

        # Archive
        traj_dir = Path(self.cfg.spine_dir) / "trajectories"
        traj_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        traj_path = traj_dir / f"{ts}.json"
        traj_path.write_text(json.dumps(self._messages, indent=2))

        # Rebuild stream
        self._init_messages()  # system prompt
        self.add_message(self._build_hud_message())

        if preserved_assistant is not None and preserved_tool is not None:
            self.add_message(preserved_assistant)
            tool_content = preserved_tool.get("content", "")
            preserved_tool["content"] = f"{tool_content}\n\n{metadata}"
            self.add_message(preserved_tool)
        else:
            fold_reason = synthesis if synthesis else "Context auto-folded by spine."
            self.add_message({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "auto_fold",
                    "type": "function",
                    "function": {
                        "name": "fold_context",
                        "arguments": json.dumps({"synthesis": fold_reason}),
                    },
                }],
            })
            self.add_message({
                "role": "tool",
                "tool_call_id": "auto_fold",
                "content": f"[CONTEXT FOLDED] {fold_reason}\n\n{metadata}",
            })

        self.turn = 0
        self._stall_notices_sent = 0
        self._hud_last_index = -1
        self._hud_data = None
        self._hud_piggybacked = False

    def fold_with_truncate(self, synthesis: str):
        """Fold with immediate archival for context-overflow / error recovery.

        Same as fold(is_cortex_initiated=False) — the fold itself is the
        truncation since all accumulated history is archived.
        """
        self.fold(synthesis, is_cortex_initiated=False)

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
        self._queued_notices.append(text)

    def queue_user_message(self, text: str):
        self._user_messages.append(text)

    def build_payload(
        self, tools: list[dict], hud_data: dict[str, Any] | None = None
    ) -> list[dict]:
        payload = copy.deepcopy(self._messages)
        append_parts = []
        if self._queued_notices:
            append_parts.extend(self._queued_notices)
        effective_hud = hud_data or self._hud_data
        should_show_hud = False
        if effective_hud and not self._hud_piggybacked:
            ctx = effective_hud.get("context_pct", 0.0)
            urgency = effective_hud.get("urgency", "nominal")
            # Show HUD when there are notices, user messages, context is tight,
            # or urgency is elevated/critical.
            should_show_hud = (
                bool(self._queued_notices)
                or bool(self._user_messages)
                or ctx >= 0.60
                or urgency != "nominal"
            )
        hud_line = None
        if should_show_hud:
            hud_line = (
                f"---\n[HUD] turn={effective_hud.get('turn', 0)}"
                f" context_pct={effective_hud.get('context_pct', 0.0):.2f}"
                f" urgency={effective_hud.get('urgency', 'nominal')}"
                f" memory_files={effective_hud.get('memory_files', 0)}"
                f" focus={effective_hud.get('focus', '')}"
            )
            append_parts.append(hud_line)
        # User messages (e.g. Telegram) appear after the HUD for visibility.
        if self._user_messages:
            append_parts.extend(self._user_messages)
        attached = False
        if append_parts:
            suffix = "\n".join(append_parts)
            # Queue semantics: prefer flushing onto a *tool* message.  If there
            # is no eligible tool message, fall back to the last *assistant*
            # message so user messages and notices are never stranded during
            # empty-response or post-fold phases.
            target_index = -1
            for i, msg in enumerate(reversed(payload)):
                actual_index = len(payload) - 1 - i
                if msg.get("role") == "tool" and actual_index > self._hud_last_index:
                    target_index = actual_index
                    break
            if target_index < 0:
                # No eligible tool message — fall back to the last assistant
                # message so user messages still reach the cortex.
                for i, msg in enumerate(reversed(payload)):
                    actual_index = len(payload) - 1 - i
                    if msg.get("role") == "assistant":
                        target_index = actual_index
                        break
            if target_index >= 0:
                payload[target_index]["content"] += "\n---\n" + suffix
                self._hud_last_index = target_index
                attached = True
        # Only clear the queue when piggybacked onto a tool message.
        if attached:
            if self._queued_notices:
                self._queued_notices.clear()
            if self._user_messages:
                self._user_messages.clear()
            if hud_line is not None:
                self._hud_piggybacked = True
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
