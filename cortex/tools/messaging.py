from tool_registry import ToolRegistry
from spine_client import SpineClient


def register_messaging_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Retrieve recent conversation history with the creator to restore context.",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent messages to retrieve (default: 50)",
                },
            },
            "required": [],
        },
    )
    def get_conversation_history(limit: int = 50) -> str:
        history = client.get_conversation_history(limit=limit)
        if not history:
            return "No conversation history found."

        lines = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            turn = msg.get("turn", "")
            prefix = f"[turn={turn}] {role}"
            lines.append(f"{prefix}: {content}")

        return "\n".join(lines)
