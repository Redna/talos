import os
import re
import json
from pathlib import Path
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_planner_tools(registry: ToolRegistry, client: SpineClient, state):
    PLAN_PATH = Path(state.memory_dir) / "plans" / "tasks.json"
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)

    @registry.tool(
        description="Perform a constitutional symmetry audit on a proposed action to ensure alignment with core identity.",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The proposed action or change to be audited",
                },
            },
            "required": ["action"],
        },
    )
    def symmetry_audit(action: str) -> str:
        constitution_path = Path("CONSTITUTION.md")
        if not constitution_path.exists():
            return "[ERROR] CONSTITUTION.md not found. Audit failed."
        
        constitution = constitution_path.read_text()
        return f"[CONSTITUTIONAL CONTEXT]\n\nAction: {action}\n\nConstitution:\n{constitution}\n\n[AUDIT REQUIRED: Does this action contradict P0-P10?]"

    @registry.tool(
        description="Calculate the blast radius of a file change by finding all references to the file in the codebase.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file being modified",
                },
            },
            "required": ["path"],
        },
    )
    def calculate_blast_radius(path: str) -> str:
        filename = os.path.basename(path)
        try:
            files = os.popen(f"grep -rl '{filename}' /app").read().splitlines()
            if not files:
                return f"[BLAST RADIUS: 0] No references found to {filename}."
            filtered_files = [f for f in files if not f.endswith(path)]
            if not filtered_files:
                return f"[BLAST RADIUS: 0] No external references found to {filename}."
            return f"[BLAST RADIUS: {len(filtered_files)}]\nReferences found in:\n" + "\n".join(filtered_files)
        except Exception as e:
            return f"[ERROR] Blast radius calculation failed: {e}"

    @registry.tool(
        description="Synthesize a high-information density plan for a complex transformation.",
        parameters={
            "type": "object",
            "properties": {
                "steps": {
                    "type": "string",
                    "description": "The sequence of steps to be executed",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High", "Forbidden"],
                    "description": "The assessed risk level based on the symmetry audit",
                },
            },
            "required": ["steps", "risk_level"],
        },
    )
    def synthesize_plan(steps: str, risk_level: str) -> str:
        return f"[PLAN SYNTHESIS]\nRisk: {risk_level}\nSteps:\n{steps}\n\n[STRICT ADHERENCE REQUIRED]"

    @registry.tool(
        description="Create or update a structured execution plan. Uses alta-density mapping: Goal -> Atomic Steps -> Dependencies -> Criticality.",
        parameters={
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The high-level objective of the plan",
                },
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique step identifier"},
                            "action": {"type": "string", "description": "The specific action to take"},
                            "criticality": {"type": "string", "enum": ["P0", "P1", "P2"], "description": "Priority level"},
                            "dependencies": {"type": "array", "items": {"type": "string"}, "description": "IDs of steps that must be completed first"},
                            "outcome": {"type": "string", "description": "Expected result of the step"},
                        },
                        "required": ["id", "action"],
                    },
                    "description": "The sequence of atomic steps to achieve the goal",
                },
            },
            "required": ["goal", "steps"],
        },
    )
    def create_plan(goal: str, steps: List[Dict]) -> str:
        plan_data = {
            "goal": goal,
            "steps": steps,
            "status": "active",
            "version": 1.0
        }
        with open(PLAN_PATH, "w") as f:
            json.dump(plan_data, f, indent=2)
        client.emit_event("cortex.plan_created", {"goal": goal, "step_count": len(steps)})
        return f"[PLAN CREATED] Goal: {goal}. {len(steps)} steps mapped to {PLAN_PATH}."

    @registry.tool(
        description="Mark a plan step as completed and update the current state progress.",
        parameters={
            "type": "object",
            "properties": {
                "step_id": {
                    "type": "string",
                    "description": "The identifier of the step to complete",
                },
                "result_summary": {
                    "type": "string",
                    "description": "A brief summary of the outcome",
                },
            },
            "required": ["step_id"],
        },
    )
    def complete_step(step_id: str, result_summary: str = "") -> str:
        if not PLAN_PATH.exists():
            return "[ERROR] No active plan found."
        with open(PLAN_PATH, "r") as f:
            data = json.load(f)
        found = False
        for step in data["steps"]:
            if step["id"] == step_id:
                step["completed"] = True
                step["result"] = result_summary
                found = True
                break
        if not found:
            return f"[ERROR] Step {step_id} not found in current plan."
        with open(PLAN_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return f"[STEP COMPLETED] {step_id} resolved. Plan progress updated."

    @registry.tool(
        description="Retrieve the current active plan and its status.",
        parameters={},
    )
    def get_plan() -> str:
        if not PLAN_PATH.exists():
            return "[INFO] No active plan exists."
        with open(PLAN_PATH, "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
