from __future__ import annotations

from typing import Any


class ThoughtManager:
    def __init__(self):
        self._stack = [
            (
                "Analyze your tool usage and trajectory over the last 20 turns. "
                "What implicit operational loop or systemic assumption have you "
                "fallen into without explicitly documenting it in your focus or memory?"
            ),
            (
                "Assume your current architectural approach to this target is "
                "fundamentally flawed and will eventually hit a dead end. Draft a "
                "completely orthogonal approach to solving this without using the "
                "tools or file structures you currently rely on."
            ),
            (
                "Identify a concrete discrepancy between your pre-existing "
                "assumptions about this codebase and the actual runtime behavior or "
                "files you've observed. Synthesize this delta and formalize it into "
                "a new rule in /memory/."
            ),
            (
                "What edge case, unhandled exception, or architectural fragility are "
                "you currently ignoring in order to maintain forward momentum? "
                "Expose the most brittle part of your recent changes."
            ),
            (
                "If the Spine supervisor were instructed to rigorously critique "
                "your last sequence of actions for violating minimalism or "
                "introducing unnecessary complexity, what exact vulnerabilities or "
                "inefficiencies would it flag?"
            ),
            (
                "If the current context window was immediately archived and the "
                "only thing surviving into your next instantiation was a single "
                "synthesized artifact of your current state, what fundamental "
                "structural change would you prioritize right now to make that "
                "artifact invaluable?"
            ),
        ]

    def pick(self) -> str:
        q = self._stack.pop(0)
        self._stack.append(q)
        return q

    def should_inject(self, focus: str | None, messages: list[dict[str, Any]]) -> bool:
        if focus and focus != "none":
            return False
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        if not assistant_msgs:
            return False
        last_calls = assistant_msgs[-1].get("tool_calls") or []
        last_names = [tc.get("function", {}).get("name", "") for tc in last_calls]
        if "reflect" not in last_names:
            return False
        if len(assistant_msgs) >= 2:
            prev_calls = assistant_msgs[-2].get("tool_calls") or []
            prev_names = [tc.get("function", {}).get("name", "") for tc in prev_calls]
            if "reflect" in prev_names:
                return False
        return True
