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
SPINE_DIR = Path(os.environ.get("SPINE_DIR", "/spine"))

LOW_VALUE_TOOLS = {"bash_command"}
LOW_VALUE_THRESHOLD = 3
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

    def is_reflect_abuse(self, max_reflect=5, window=10):
        """Detect excessive reflect calls with sleep_duration=0 in recent history."""
        recent = list(self.history)[-window:]
        reflect_count = 0
        for name, args_key in recent:
            if name == "reflect":
                try:
                    args = json.loads(args_key)
                    if args.get("sleep_duration", 0) == 0:
                        reflect_count += 1
                except Exception:
                    reflect_count += 1
        return reflect_count >= max_reflect

    def reset(self):
        self.history.clear()


def _build_hud(state, context_pct=0.0, turn=0):
    memory_dir = state.memory_dir
    md_files = list(memory_dir.glob("*.md")) if memory_dir.exists() else []
    urgency = "nominal"
    if state.error_streak >= 3:
        urgency = "elevated"
    if state.error_streak >= 5:
        urgency = "critical"
    return {
        "turn": turn,
        "context_pct": context_pct,
        "urgency": urgency,
        "memory_files": len(md_files),
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
    context_pct = 0.0

    while True:
        paused = (SPINE_DIR / ".paused").exists()
        single_step = (SPINE_DIR / ".single_step").exists()
        was_single_step = single_step
        try:
            if paused and not single_step:
                time.sleep(1)
                continue

            if single_step:
                (SPINE_DIR / ".single_step").unlink(missing_ok=True)

            hud_data = _build_hud(state, context_pct=context_pct, turn=turn)

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

            context_pct = response.get("context_pct", 0.0)
            turn = response.get("turn", 0)
            hud_data = _build_hud(state, context_pct=context_pct, turn=turn)

            state.total_tokens_consumed += response.get("tokens_used", 0)
            state.save()
            state.error_streak = 0
            state.save()

            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                continue

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

                # Reflect abuse guard: block reflect with sleep_duration=0 if used too frequently
                if tool_name == "reflect" and detector.is_reflect_abuse():
                    blocked = (
                        "[BLOCKED] reflect has been called too frequently with sleep_duration=0. "
                        "You are in a degenerate loop. You MUST call list_files, read_file, write_file, or bash_command next. "
                        "Your focus has been cleared. Pick a new objective immediately."
                    )
                    client.tool_result(tc["id"], blocked, False)
                    state.current_focus = None
                    state.save()
                    detector.reset()
                    break

                if detector.is_stalled():
                    report = detector.get_stall_report()
                    print(f"[Cortex] Stall detected mid-loop: {report}")
                    client.emit_event("cortex.stall_detected", {"report": report})

                    if tool_name == "reflect":
                        # Hard auto-break for reflect loops: mark as failed,
                        # clear focus, and force the LLM to pick a different tool.
                        blocked = (
                            f"{report}\n"
                            "[BLOCKED] reflect is disabled after repeated consecutive use. "
                            "You MUST call list_files, read_file, write_file, or bash_command next. "
                            "Your focus has been cleared. Pick a new objective immediately."
                        )
                        client.tool_result(tc["id"], blocked, False)
                        state.current_focus = None
                        state.save()
                        detector.reset()
                        break

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
        finally:
            if was_single_step:
                (SPINE_DIR / ".paused").touch(exist_ok=True)


if __name__ == "__main__":
    main()
