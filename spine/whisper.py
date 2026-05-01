from __future__ import annotations


class WhisperManager:
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

    def should_whisper(self, focus: str | None, messages: list[dict]) -> bool:
        if focus and focus != "none":
            return False
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if not tool_msgs:
            return False
        if "[REFLECT]" not in tool_msgs[-1].get("content", ""):
            return False
        if len(tool_msgs) >= 2 and "[REFLECT]" in tool_msgs[-2].get("content", ""):
            return False
        return True
