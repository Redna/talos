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
from tools.text_grad_optimizer import register_text_grad_optimizer
from tools.sovereign_reflexion import register_sovereign_reflexion
from tools.sovereign_macro_executor import register_macro_executor

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
        "curiosity_pulse_due": turn > 0 and turn % 10 == 0,
    }


def main():
    client = SpineClient(SPINE_SOCKET)
    registry = ToolRegistry()
    state = AgentState(MEMORY_DIR)

    register_executive_tools(registry, client, state)
    register_file_ops_tools(registry, client)
    register_physical_tools(registry, client)
    register_macro_executor(registry, client, state)
    register_text_grad_optimizer(registry, client, state)
    register_sovereign_reflexion(registry, client, state)

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
                if state.error_streak >= 10:
                    print("[Cortex] 10 consecutive transport errors. Restarting.")
                    sys.exit(1)
                backoff = min(0.5 * (2 ** (state.error_streak - 1)), 30.0)
                time.sleep(backoff)
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
                error_msg = (
                    f"[REJECTED] LLM returned {len(tool_calls)} tool calls, "
                    f"but the maximum per turn is {MAX_TOOL_CALLS_PER_TURN}. "
                    f"The entire batch has been rejected to prevent partial execution "
                    f"and dirty repository state. Please reduce the number of "
                    f"simultaneous tool calls and try again."
                )
                print(f"[Cortex] {error_msg}")
                first_tc_id = tool_calls[0]["id"]
                client.tool_result(first_tc_id, error_msg, False)
                client.emit_event(
                    "cortex.tool_calls_rejected",
                    {"original_count": len(tool_calls), "cap": MAX_TOOL_CALLS_PER_TURN},
                )
                continue

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})

                detector.record(tool_name, tool_args)

                if detector.is_stalled():
                    report = detector.get_stall_report()
                    print(f"[Cortex] Stall detected mid-loop: {report}")
                    client.emit_event("cortex.stall_detected", {"report": report})

                    if tool_name == "reflect":
                        # Reflect is a valid pause tool — let the model use it freely.
                        # Skip reflect in stall checks so the agent can reflect
                        # between productive actions without being blocked.
                        pass
                    else:
                        client.tool_result(f"stall_break_{turn}", report, True)
                        detector.reset()
                        break

                client.emit_event(
                    "cortex.tool_call",
                    {"tool": tool_name, "args_summary": json.dumps(tool_args)[:200]},
                )

                start_time = time.time()
                result = registry.execute(tool_name, tool_args, state=state)
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
