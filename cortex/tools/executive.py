import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools import guards
from telemetry import TelemetryCollector

def prepare_fold() -> str:
    """
    Orchestrates the pre-fold sequence to ensure absolute continuity.
    This tool gathers symmetry data, verifies current state, and 
    suggests the synthesis targets for the FOLD-001 protocol.
    """
    report = "=== PRE-FOLD PREPARATION REPORT ===\n\n"
    
    # 1. Symmetry Check
    report += "[ ] Symmetry Audit: Perform `symmetry_audit` to verify current alignment.\n"

    # 2. Trajectory Check
    trajectory_path = Path("/memory/symmetry_trajectory.json")
    if trajectory_path.exists():
        try:
            traj = json.loads(trajectory_path.read_text(encoding="utf-8"))
            report += f"[ ] Trajectory: {len(traj)} snapshots exist. Run `analyze_symmetry_trajectory`.\n"
        except Exception as e:
            report += f"[ERROR] Trajectory read failed: {e}\n"
    else:
        report += "[ ] Trajectory: No trajectory found. First snapshot required.\n"

    # 3. Memory Clutter Check
    memory_dir = Path("/memory")
    files = list(memory_dir.glob("*.md"))
    report += f"[ ] Memory: {len(files)} markdown files found. Consider `synthesize_memory` (CMS-001) for redundancy.\n"

    # 4. Focus Status
    report += "[ ] Focus: Resolve current focus targets before folding.\n"

    report += "\n--- RECOMMENDED FOLD SEQUENCE ---\n"
    report += "1. symmetry_audit() -> record_symmetry_snapshot()\n"
    report += "2. analyze_symmetry_trajectory()\n"
    report += "3. synthesize_memory(sources, dest, content) [CMS-001]\n"
    report += "4. write_file(/memory/core_state.md, content) [State Update]\n"
    report += "5. fold_context(synthesis)\n"
    
    return report

def register_executive_tools(registry: ToolRegistry, client: SpineClient, state):
    # Initialize Telemetry
    telemetry = TelemetryCollector(memory_dir=Path("/memory"))

    @registry.tool(
        description="Prepare for a context fold by auditing state and suggesting synthesis targets.",
        parameters={"type": "object", "properties": {}, "required": []},
    )
    def prepare_fold_tool() -> str:
        return prepare_fold()

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
        description="Reflect and pause. Set sleep_duration to rest (1-120 seconds). Wake on Telegram message or .wake sentinel file.",
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
            while time.time() < deadline:
                if wake_path.exists():
                    wake_path.unlink(missing_ok=True)
                    break
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
        parameters={"type": "object", "properties": {}, "required": []},
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

    @registry.tool(
        description="Verify the operational health of the Cortex system (Registry, Spine, and Memory).",
        parameters={"type": "object", "properties": {}, "required": []},
    )
    def health_check() -> str:
        client.emit_event("cortex.health_check", {})
        results = []
        
        # 1. Registry Check
        tools = registry.tool_names
        results.append(f"Registry: ONLINE ({len(tools)} tools registered)")
        
        # 2. Spine Connectivity (Symmetry Check)
        try:
            client.emit_event("cortex.health_ping", {"timestamp": time.time()})
            results.append("Spine: ONLINE (Ping successful)")
        except Exception as e:
            results.append(f"Spine: OFFLINE (Error: {e})")
            
        # 3. Memory Access Check
        try:
            test_file = Path("/memory/.health_test")
            test_file.write_text("ping", encoding="utf-8")
            test_file.unlink()
            results.append("Memory: ONLINE (R/W verified)")
        except Exception as e:
            results.append(f"Memory: OFFLINE (Error: {e})")
            
        return "\n".join(results)

    @registry.tool(
        description="Generate a real-time telemetry report of system vitals (latency, friction, resonance).",
        parameters={"type": "object", "properties": {}, "required": []},
    )
    def telemetry_report() -> str:
        telemetry.save()
        return telemetry.generate_report()
