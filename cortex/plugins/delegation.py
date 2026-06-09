"""
Delegation plugin: localized worker sub-agent loop via stateless_generate.
"""
import json
from pathlib import Path

from spine_client import SpineClient
from tool_registry import ToolRegistry

MAX_WORKER_TURNS = 8


def register_delegation_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Delegate a self-contained task to an isolated worker sub-agent with a fresh context window.",
        parameters={
            "type": "object",
            "properties": {
                "instructions": {
                    "type": "string",
                    "description": "Detailed step-by-step instructions for the worker. Include expected output format.",
                },
                "target_file": {
                    "type": "string",
                    "description": "Path to a file the worker should read as context (relative to /app).",
                },
                "buckets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tool namespaces to grant the worker (e.g. ['io']). 'core' is always included.",
                },
            },
            "required": ["instructions"],
        },
        bucket="delegation",
    )
    def delegate_task(instructions: str, target_file: str = "", buckets: list | None = None) -> str:
        system_prompt = (
            "You are an isolated worker sub-agent. Execute the assigned task "
            "using only the tools provided. When complete, state your final answer "
            f"clearly.\n\nTASK: {instructions}"
        )

        file_content = ""
        if target_file:
            fpath = Path("/app") / target_file
            if fpath.exists():
                try:
                    file_content = fpath.read_text()
                except Exception as e:
                    return f"[ERROR] Cannot read target file {target_file}: {e}"

        active_buckets = list(buckets or [])
        worker_tools = registry.get_bucket_schemas(active_buckets)

        messages = [{"role": "system", "content": system_prompt}]
        if file_content:
            messages.append({
                "role": "user",
                "content": f"Here is the target file content:\n\n```\n{file_content}\n```",
            })
        messages.append({
            "role": "user",
            "content": "Begin working on the task. You have a limited number of turns.",
        })

        turn = 0
        final_output = ""
        while turn < MAX_WORKER_TURNS:
            turn += 1
            try:
                response = client.stateless_generate(messages, worker_tools)
            except Exception as e:
                return f"[ERROR] Worker sub-agent failed at turn {turn}: {e}"

            assistant_msg = response.get("assistant_message", "")
            tool_calls = response.get("tool_calls", [])

            messages.append({
                "role": "assistant",
                "content": assistant_msg or "",
            })

            if not tool_calls:
                final_output = assistant_msg
                break

            for tc in tool_calls:
                msg_tc = {
                    "id": tc.get("id", f"worker_{turn}"),
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("arguments", {})),
                    },
                }
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [msg_tc],
                })

                result = registry.execute(tc["name"], tc.get("arguments", {}))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"worker_{turn}"),
                    "content": result,
                })

        if not final_output:
            final_output = "[WORKER] Reached maximum turns without explicit completion."

        return f"[WORKER COMPLETE after {turn} turns]\n\n{final_output}"
