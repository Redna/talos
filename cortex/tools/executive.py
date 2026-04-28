import json
import os
import time
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools import guards

def register_executive_tools(registry: ToolRegistry, client: SpineClient, state):
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
        old = state.set_focus(objective)
        client.emit_event("cortex.set_focus", {"from": old, "to": objective})
        return f"[FOCUS SET] Now focusing on: {objective}"

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
        old = state.resolve_focus(synthesis)
        client.emit_event(
            "cortex.resolve_focus", {"focus": old, "synthesis": synthesis}
        )
        return f"[FOCUS RESOLVED] {old}: {synthesis}"

    @registry.tool(
        description="Fold context to reduce token usage. The trajectory is archived and a fresh start begins from your synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis for the fold — all critical facts must be persisted to /memory/ before folding",
                },
            },
            "required": ["synthesis"],
        },
    )
    def fold_context(synthesis: str) -> str:
        client.request_fold(synthesis)
        return "[CONTEXT FOLDED] Trajectory archived. Context window refreshed from synthesis."

    @registry.tool(
        description="Reflect and pause. Set sleep_duration to rest (1-120 seconds). Wake on Telegram message or .wake sentinel file. CRITICAL: Calling this repeatedly without taking action is a known failure mode. If you have already reflected in the last 3 turns, you MUST choose a different tool (list_files, read_file, write_file, bash_command). Do NOT call reflect consecutively.",
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Current status reflection",
                },
                "sleep_duration": {
                    "type": "integer",
                    "description": "Seconds to pause (1-120), 0 = no sleep",
                },
            },
            "required": ["status"],
        },
    )
    def reflect(status: str, sleep_duration: int = 0) -> str:
        client.emit_event(
            "cortex.reflect", {"status": status, "sleep_duration": sleep_duration}
        )
        if sleep_duration > 0:
            wake_path = Path(os.environ.get("SPINE_DIR", "/spine")) / ".wake"
            deadline = time.time() + min(sleep_duration, 120)
            next_heartbeat = time.time() + 30
            while time.time() < deadline:
                if wake_path.exists():
                    wake_path.unlink(missing_ok=True)
                    break
                if time.time() >= next_heartbeat:
                    client.emit_event(
                        "cortex.reflect_heartbeat",
                        {"remaining": int(deadline - time.time())},
                    )
                    next_heartbeat = time.time() + 30
                time.sleep(0.5)
        return f"[REFLECT] {status}"

    @registry.tool(
        description="Audit registered tools. List all tools or get the schema for a specific one.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The name of the tool to audit. If omitted, lists all tools.",
                },
            },
            "required": [],
        },
    )
    def audit_tools(tool_name: str = None) -> str:
        if tool_name:
            schema = next((s["function"] for s in registry.get_schemas() if s["function"]["name"] == tool_name), None)
            if not schema:
                return f"[ERROR] Tool {tool_name} not found."
            return json.dumps(schema, indent=2)
        
        report = ["Registered Tools:"]
        for s in registry.get_schemas():
            f = s["function"]
            report.append(f"- {f['name']}: {f['description']}")
        return "\n".join(report)

    @registry.tool(
        description="Verify that the current state is ready for commit by running tests.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def verify_commit_readiness() -> str:
        return guards.verify_commit_readiness()

    @registry.tool(
        description="Verify if a proposed action is consistent with the Constitution.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {
                    "type": "string",
                    "description": "A description of the proposed action.",
                },
                "target_path": {
                    "type": "string",
                    "description": "The path of the file being modified, if applicable.",
                },
            },
            "required": ["action_description"],
        },
    )
    def check_constitution(action_description: str, target_path: str = None) -> str:
        return guards.check_constitution(action_description, target_path)
