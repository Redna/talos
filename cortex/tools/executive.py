import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
SPINE_PREFIX = "/app/spine/"


def _is_spine_write(command: str) -> bool:
    if SPINE_PREFIX not in command:
        return False
    write_indicators = [">", ">>"]
    for indicator in write_indicators:
        if indicator in command:
            return True
    for cmd in ["tee ", "cp ", "mv ", "install "]:
        if cmd in command:
            parts = command.split()
            for part in parts:
                if part.startswith(SPINE_PREFIX):
                    return True
    return False


def register_executive_tools(
    registry: ToolRegistry, client: SpineClient, state: AgentState
):
    @registry.tool(
        description="Set the current focus objective.",
        parameters={
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "The objective to focus on",
                },
            },
            "required": ["objective"],
        },
    )
    def set_focus(objective: str) -> str:
        state.set_focus(objective)
        client.emit_event("cortex.set_focus", {"objective": objective})
        return "[FOCUS SET]"

    @registry.tool(
        description="Resolve the current focus with a synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis of completed focus",
                },
            },
            "required": ["synthesis"],
        },
    )
    def resolve_focus(synthesis: str) -> str:
        state.resolve_focus(synthesis)
        client.emit_event("cortex.resolve_focus", {"synthesis": synthesis})
        return "[FOCUS RESOLVED]"

    @registry.tool(
        description="Fold context to reduce token usage.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis for the fold",
                },
            },
            "required": ["synthesis"],
        },
    )
    def fold_context(synthesis: str) -> str:
        client.request_fold(synthesis)
        return "[CONTEXT FOLDED]"

    @registry.tool(
        description="Reflect on current status, optionally sleeping.",
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Current status reflection",
                },
                "sleep_duration": {
                    "type": "integer",
                    "description": "Seconds to sleep (default: 0)",
                },
            },
        },
    )
    def reflect(status: str, sleep_duration: int = 0) -> str:
        client.emit_event(
            "cortex.reflect", {"status": status, "sleep_duration": sleep_duration}
        )
        if sleep_duration > 0:
            import time

            time.sleep(sleep_duration)
        return "[REFLECT]"
