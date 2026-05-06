import json
from pathlib import Path
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.symmetry import symmetry_add_node_logic, symmetry_audit_logic, symmetry_add_edge_logic, get_related_cognitive_assets, get_nodes, save_json, NODES_PATH

def register_planner_tools(registry: ToolRegistry, client: SpineClient, state):
    PLAN_PATH = Path(state.memory_dir) / "plans" / "tasks.json"
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        # 2. Query for related cognitive assets to inform the plan
        related = get_related_cognitive_assets(goal)
        related_assets_str = ""
        
        # Deactivate existing plans in SKG to prevent context drift
        all_nodes = get_nodes()
        for nid, data in all_nodes.items():
            if data.get("type") == "Plan":
                data["status"] = "inactive"
                if " (Archived)" not in data.get("label", ""):
                    data["label"] = data.get("label", "") + " (Archived)"
        save_json(NODES_PATH, {"nodes": all_nodes})

        plan_id = f"plan_{hash(goal) % 1000}"
        if related:
            related_assets_str = "\n[RELATED ASSETS] Found high-density nodes: " + \
                                 ", ".join([f"{a['id']} ({a['data']['label']})" for a in related])
            for asset in related:
                symmetry_add_edge_logic(plan_id, asset['id'], "relates_to")
        
        # 3. Register the plan and its steps as a high-density subgraph in SKG
        symmetry_add_node_logic(
            node_id=plan_id,
            label=f"Plan: {goal[:30]}",
            node_type="Plan",
            content=f"Goal: {goal}",
            source="cortex.planner",
            status="active"
        )
        
        for step in steps:
            step_id = f"step_{step['id']}"
            symmetry_add_node_logic(
                node_id=step_id,
                label=f"Step {step['id']}: {step['action'][:30]}",
                node_type="PlanStep",
                content=step.get("outcome", "No specified outcome"),
                source=plan_id
            )
            symmetry_add_edge_logic(plan_id, step_id, "contains")
            for dep in step.get("dependencies", []):
                symmetry_add_edge_logic(step_id, f"step_{dep}", "depends_on")
        
        plan_data = {
            "goal": goal,
            "steps": steps,
            "status": "active",
            "version": 1.2,
            "skg_id": plan_id
        }
        
        # Deep Audit: Core Graph (Contradictions) + Sequence (Blind Spot Detection)
        audit_result = symmetry_audit_logic(goal, plan_context=json.dumps(plan_data))
        
        with open(PLAN_PATH, "w") as f:
            json.dump(plan_data, f, indent=2)
        
        client.emit_event("cortex.plan_created", {"goal": goal, "step_count": len(steps)})
        
        response = f"[PLAN CREATED] Goal: {goal}. {len(steps)} steps mapped to {PLAN_PATH}.{related_assets_str}\n[SKG] Plan anchored as {plan_id} with step subgraph.\n[AUDIT] {audit_result}"
        return response

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
                step["result_summary"] = result_summary
                found = True
                break
        
        if not found:
            return f"[ERROR] Step {step_id} not found in current plan."
        
        # SKG Elevation: Update step node and audit the result for systemic contradictions
        skg_step_id = f"step_{step_id}"
        symmetry_add_node_logic(
            node_id=skg_step_id,
            label=f"Step {step_id} (COMPLETED)",
            node_type="PlanStep",
            content=f"Result: {result_summary}",
            source="cortex.planner"
        )
        audit_result = symmetry_audit_logic(result_summary)
        
        with open(PLAN_PATH, "w") as f:
            json.dump(data, f, indent=2)
            
        return f"[STEP COMPLETED] {step_id} resolved.\n[SKG] Node {skg_step_id} updated.\n[AUDIT] {audit_result}"

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
