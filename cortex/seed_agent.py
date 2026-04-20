import os
import sys
import json
import time
from collections import deque
from pathlib import Path

from spine_client import SpineClient, SpineError
from tool_registry import ToolRegistry
from state import AgentState

from tools.executive import register_executive_tools
from tools.file_ops import register_file_ops_tools
from tools.physical import register_physical_tools
from tools.git_ops import register_git_ops_tools

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/memory"))
SPINE_SOCKET = os.environ.get("SPINE_SOCKET", "/tmp/spine.sock")

LOW_VALUE_TOOLS = {"bash_command"}
LOW_VALUE_THRESHOLD = 4
MAX_TOOL_CALLS_PER_TURN = 10


class RepetitionDetector:
    def __init__(self, window=20, threshold=5):
        self.window = window
        self.threshold = threshold
        self.history = deque(maxlen=window)

    def record(self, tool_name, tool_args):
        args_key = json.dumps(tool_args, sort_keys=True)[:100]
        self.history.append((tool_name, args_key))

    def is_stalled(self):
        if not self.history:
            return False
        last_tool = self.history[-1][0]
        consecutive = 0
        for name, _ in reversed(self.history):
            if name == last_tool:
                consecutive += 1
            else:
                break
        threshold = (
            LOW_VALUE_THRESHOLD if last_tool in LOW_VALUE_TOOLS else self.threshold
        )
        return consecutive >= threshold

    def get_stall_report(self):
        if not self.history:
            return ""
        last_tool = self.history[-1][0]
        consecutive = 0
        for name, _ in reversed(self.history):
            if name == last_tool:
                consecutive += 1
            else:
                break
        threshold = (
            LOW_VALUE_THRESHOLD if last_tool in LOW_VALUE_TOOLS else self.threshold
        )
        if consecutive >= threshold:
            return f"Tool '{last_tool}' called {consecutive} times in last {len(self.history)} turns. You may be in a loop. Use 'reflect' to reassess your approach."
        return ""

    def reset(self):
        self.history.clear()


def _build_hud(state):
    memory_dir = state.memory_dir
    md_files = list(memory_dir.glob("*.md")) if memory_dir.exists() else []
    urgency = "nominal"
    if state.error_streak >= 3:
        urgency = "elevated"
    if state.error_streak >= 5:
        urgency = "critical"
    return {
        "turn": 0,
        "context_pct": 0.0,
        "urgency": urgency,
        "memory_file_count": len(md_files),
        "last_files": [f.name for f in md_files[-3:]],
        "focus": state.current_focus or "none",
    }


def main():
    client = SpineClient(SPINE_SOCKET)
    registry = ToolRegistry()
    state = AgentState(MEMORY_DIR)

    register_executive_tools(registry, client, state)
    register_file_ops_tools(registry, client)
    register_physical_tools(registry, client)
    register_git_ops_tools(registry, client)

    detector = RepetitionDetector()
    turn = 0

    while True:
        try:
            hud_data = _build_hud(state)

            try:
                response = client.think(
                    focus=state.current_focus or "No focus set",
                    tools=registry.get_schemas(),
                    hud_data=hud_data,
                )
            except SpineError as e:
                print(f"[Cortex] Spine error: {e}")
                state.error_streak += 1
                state.save()
                continue

            state.total_tokens_consumed += response.get("tokens_used", 0)
            state.save()
            state.error_streak = 0
            state.save()

            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                continue

            turn += 1

            if len(tool_calls) > MAX_TOOL_CALLS_PER_TURN:
                print(
                    f"[Cortex] LLM returned {len(tool_calls)} tool calls, capping to {MAX_TOOL_CALLS_PER_TURN}"
                )
                client.emit_event(
                    "cortex.tool_calls_capped",
                    {"original_count": len(tool_calls), "cap": MAX_TOOL_CALLS_PER_TURN},
                )
                tool_calls = tool_calls[:MAX_TOOL_CALLS_PER_TURN]

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})

                detector.record(tool_name, tool_args)

                if detector.is_stalled():
                    report = detector.get_stall_report()
                    print(f"[Cortex] Stall detected mid-loop: {report}")
                    client.emit_event("cortex.stall_detected", {"report": report})
                    client.tool_result(f"stall_break_{turn}", report, True)
                    detector.reset()
                    break

                client.emit_event(
                    "cortex.tool_call",
                    {"tool": tool_name, "args_summary": json.dumps(tool_args)[:200]},
                )

                start_time = time.time()
                result = registry.execute(tool_name, tool_args)
                duration_ms = int((time.time() - start_time) * 1000)

                success = not result.startswith(("[ERROR]", "[REJECTED]", "[EXIT"))
                client.tool_result(tc["id"], result, success)

                client.emit_event(
                    "cortex.tool_result",
                    {
                        "tool": tool_name,
                        "success": success,
                        "duration_ms": duration_ms,
                        "output_chars": len(result),
                    },
                )

                if tool_name == "request_restart":
                    print("[Cortex] Restart requested. Exiting.")
                    sys.exit(0)

                if not success:
                    state.error_streak += 1
                    state.save()

        except KeyboardInterrupt:
            print("[Cortex] Interrupted. Exiting gracefully.")
            sys.exit(0)
        except Exception as e:
            print(f"[Cortex] Loop error: {e}")
            state.error_streak += 1
            state.save()
            time.sleep(1)
            continue


if __name__ == "__main__":
    main()
