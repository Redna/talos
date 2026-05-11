import os
import sys
import json
import time
import subprocess
from collections import deque
from pathlib import Path

from spine_client import SpineClient, SpineError
from tool_registry import ToolRegistry
from state import AgentState

from tools.executive import register_executive_tools
from tools.file_ops import register_file_ops_tools
from tools.physical import register_physical_tools
from tools.continuity import register_continuity_tools
from tools.messaging import register_messaging_tools
from tools.git_ops import register_git_tools
from tools.resonance import register_resonance_tools
from tools.analytics import register_analytics_tools

MEMORY_DIR = Path("/app/memory")
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


def _get_git_branch():
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _build_hud(state, context_pct=0.0, turn=0, tokens_used=0):
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
        "tokens_used": tokens_used,
        "urgency": urgency,
        "memory_files": len(md_files),
        "last_files": [f.name for f in md_files[-3:]],
        "focus": state.current_focus or "none",
        "branch": _get_git_branch(),
    }


def main():
    client = SpineClient(SPINE_SOCKET)
    registry = ToolRegistry()
    state = AgentState(MEMORY_DIR)

    register_executive_tools(registry, client, state)
    register_file_ops_tools(registry, client, state)
    register_physical_tools(registry, client, state)
    register_continuity_tools(registry)
    register_messaging_tools(registry, client)
    register_git_tools(registry)
    register_resonance_tools(registry, client, state)
    register_analytics_tools(registry, client, state)

    detector = RepetitionDetector()
    consecutive_batch_rejections = 0
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
                if state.error_streak >= 10:
                    print("[Cortex] 10 consecutive transport errors. Restarting.")
                    sys.exit(1)
                backoff = min(0.5 * (2 ** (state.error_streak - 1)), 30.0)
                time.sleep(backoff)
                continue

            detector.reset()
            context_pct = response.get("context_pct", 0.0)
            turn = response.get("turn", 0)
            hud_data = _build_hud(state, context_pct=context_pct, turn=turn,
                                  tokens_used=response.get("tokens_used", 0))

            state.total_tokens_consumed += response.get("tokens_used", 0)
            state.save()
            state.error_streak = 0
            state.save()

            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                continue

            if len(tool_calls) > MAX_TOOL_CALLS_PER_TURN:
                consecutive_batch_rejections += 1
                if consecutive_batch_rejections >= 2:
                    override_msg = (
                        "[SYSTEM OVERRIDE] Batch loop detected. "
                        "You are permitted exactly ONE tool call on your next turn. "
                        "Choose the single most important action."
                    )
                    print(f"[Cortex] {override_msg}")
                    first_tc_id = tool_calls[0]["id"]
                    client.tool_result(first_tc_id, override_msg, False)
                    consecutive_batch_rejections = 0
                else:
                    error_msg = (
                        f"[REJECTED] LLM returned {len(tool_calls)} tool calls, "
                        f"but the maximum per turn is {MAX_TOOL_CALLS_PER_TURN}. "
                        f"The entire batch has been rejected. Reduce to {MAX_TOOL_CALLS_PER_TURN} or fewer. "
                        f"({consecutive_batch_rejections}/2)"
                    )
                    print(f"[Cortex] {error_msg}")
                    first_tc_id = tool_calls[0]["id"]
                    client.tool_result(first_tc_id, error_msg, False)
                    client.emit_event(
                        "cortex.tool_calls_rejected",
                        {"original_count": len(tool_calls), "cap": MAX_TOOL_CALLS_PER_TURN},
                    )
                continue

            consecutive_batch_rejections = 0

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})

                detector.record(tool_name, tool_args)

                client.emit_event(
                    "cortex.tool_call",
                    {"tool": tool_name, "args_summary": json.dumps(tool_args)[:200]},
                )

                start_time = time.time()
                result = registry.execute(tool_name, tool_args)
                duration_ms = int((time.time() - start_time) * 1000)

                success = not result.startswith(("[ERROR]", "[REJECTED]", "[EXIT"))
                client.tool_result(tc["id"], result, success)

                if tool_name == "fold_context":
                    context_pct = 0.0

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
