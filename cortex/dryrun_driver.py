"""
Dry-run cortex driver.

Loaded by ``seed_agent.py`` when ``TALOS_DRYRUN_MODE`` is set.  This
replaces only the LLM-decision parts of the agent loop — the IPC
machinery (SpineClient, ToolRegistry, tool_result calls) is the real
production code path.  The driver just chooses which tool call to
issue next based on the mode.

Three modes:

  - ``happy`` — same as a normal cortex: every turn is a
    ``bash_command`` echo.  No crashes, no stalls.

  - ``crash`` — first N turns are normal ``bash_command`` calls.
    On turn ``T`` the driver calls ``request_restart`` with a
    canned reason and then ``sys.exit(0)``.  The supervisor sees
    the process exit and counts a failure.

  - ``stall`` — first N turns are normal ``bash_command`` calls.
    On turn ``T`` the driver calls ``reflect`` with
    ``sleep_duration=10000`` and never returns.  The HealthMonitor
    notices the missing events and the supervisor SIGKILLs the
    nono Popen.

Why a separate module and not monkey-patches inside seed_agent.py
-----------------------------------------------------------------
Keeping the mode selector in its own file means ``seed_agent.py``
stays close to production.  The only change to ``seed_agent.py``
is one ``import`` guarded by an env var.  If the env var is not
set (the normal production case) the dryrun driver is never
imported — zero runtime overhead and zero risk of accidentally
exercising the dryrun path in production.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

# Environment knobs — these are read once at import time.
DRYRUN_MODE = os.environ.get("TALOS_DRYRUN_MODE", "").strip().lower()
DRYRUN_CRASH_AT_TURN = int(os.environ.get("TALOS_DRYRUN_CRASH_AT_TURN", "6"))
DRYRUN_STALL_AT_TURN = int(os.environ.get("TALOS_DRYRUN_STALL_AT_TURN", "4"))
DRYRUN_CRASH_REASON = os.environ.get(
    "TALOS_DRYRUN_CRASH_REASON", "simulated crash from dry-run"
)
DRYRUN_STALL_SLEEP = int(os.environ.get("TALOS_DRYRUN_STALL_SLEEP", "10000"))


def is_active() -> bool:
    """True if the dry-run driver should intercept the LLM loop."""
    return DRYRUN_MODE in ("happy", "crash", "stall")


def current_mode() -> str:
    """The active mode (or ``""`` if disabled)."""
    return DRYRUN_MODE if is_active() else ""


@dataclass
class DryRunPlan:
    """The tool call to issue on a given turn.

    The plan is a tiny stand-in for an LLM response: it carries the
    tool name, the JSON arguments, and an optional control flow
    directive (``exit_after`` / ``sleep_after``).  The seed_agent
    imports this dataclass, builds a plan via :func:`plan_next`, then
    converts it into the OpenAI ``tool_calls`` format the rest of
    the cortex already understands.
    """
    tool_name: str
    arguments: dict
    exit_after: bool = False
    sleep_after: int = 0  # seconds


def _bash_echo(turn: int) -> DryRunPlan:
    return DryRunPlan(
        tool_name="bash_command",
        arguments={"command": f"echo 'dry-run cycle {turn}'"},
    )


def _request_restart(reason: str) -> DryRunPlan:
    return DryRunPlan(
        tool_name="request_restart",
        arguments={"reason": reason},
        exit_after=True,
    )


def _reflect_stall(sleep_seconds: int, status: str) -> DryRunPlan:
    return DryRunPlan(
        tool_name="reflect",
        arguments={"status": status, "sleep_duration": sleep_seconds},
        sleep_after=sleep_seconds,
    )


def plan_next(turn: int) -> DryRunPlan:
    """Return the plan for the *next* cortex turn.

    The turn index is 1-based and supplied by the caller.  For
    ``happy`` mode this is a never-ending sequence of bash echoes.
    For ``crash`` mode the plan is bash echoes until the configured
    turn, then a single ``request_restart`` followed by ``exit``.
    For ``stall`` mode the plan is bash echoes until the configured
    turn, then ``reflect(sleep_duration=10000)`` and the cortex
    blocks forever.
    """
    if not is_active():
        # Defensive: callers must check is_active() first.  Fall back
        # to a single bash echo so the agent still does *something*
        # useful rather than crashing on a missing branch.
        return _bash_echo(turn)

    if DRYRUN_MODE == "happy":
        return _bash_echo(turn)

    if DRYRUN_MODE == "crash":
        if turn < DRYRUN_CRASH_AT_TURN:
            return _bash_echo(turn)
        return _request_restart(DRYRUN_CRASH_REASON)

    if DRYRUN_MODE == "stall":
        if turn < DRYRUN_STALL_AT_TURN:
            return _bash_echo(turn)
        return _reflect_stall(DRYRUN_STALL_SLEEP, "simulated stall from dry-run")

    return _bash_echo(turn)


def plan_to_openai_tool_call(plan: DryRunPlan, turn: int) -> dict:
    """Convert a plan into the OpenAI tool_call dict the Spine expects.

    The Spine parses the response from the Gate and returns a
    ``tool_calls`` list of dicts with ``id``, ``name``, and
    ``arguments``.  The Cortex receives this and dispatches to the
    registered tool.  We just need to match that shape.
    """
    import json
    return {
        "id": f"call_{turn:04d}",
        "type": "function",
        "function": {
            "name": plan.tool_name,
            "arguments": json.dumps(plan.arguments),
        },
    }


def should_exit(plan: DryRunPlan) -> bool:
    """Whether the cortex should ``sys.exit`` after this tool call."""
    return plan.exit_after


def should_block(plan: DryRunPlan) -> bool:
    """Whether the cortex should block forever after this tool call.

    In practice the registered ``reflect`` tool handles the sleep
    internally — this function exists so the cortex's main loop
    has a single check.
    """
    return plan.sleep_after > 0
