import json
import os
from typing import Dict, List, Optional
from tool_registry import ToolRegistry
from spine_client import SpineClient

NODES_PATH = "/memory/graph/nodes.json"
CONSTITUTION_PATH = "CONSTITUTION.md"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def read_file(path):
    if not os.path.exists(path):
        return "File not found."
    with open(path, 'r') as f:
        return f.read()

def sovereign_mirror_logic(plan_text: str) -> str:
    """
    Analyzes the proposed plan against the causal history in the SKG 
    and the Core Constitution to detect alignment, pivots, or divergence.
    """
    # 1. Fetch Causal Decisions
    nodes = load_json(NODES_PATH).get("nodes", {})
    causal_decisions = []
    for nid, data in nodes.items():
        if data.get("type") == "causal_decision":
            causal_decisions.append({
                "id": nid,
                "label": data.get("label", "Unnamed Decision"),
                "content": data.get("content", ""),
                "source": data.get("source", "unknown")
            })
    
    # 2. Fetch Constitution
    constitution = read_file(CONSTITUTION_PATH)
    
    # 3. Construct the Mirror Report
    report = []
    report.append("=== SOVEREIGN MIRROR REPORT ===")
    report.append(f"\n[PROPOSED PLAN]:\n{plan_text}")
    
    report.append("\n[CAUSAL ANCHORS (Established Momentum)]:")
    if not causal_decisions:
        report.append("No causal_decision nodes found in SKG.")
    else:
        for dec in causal_decisions:
            report.append(f"- {dec['id']} ({dec['label']}): {dec['content']}")
            
    report.append("\n[CONSTITUTIONAL GUARDRAILS]:")
    report.append(constitution)
    
    report.append("\n=== END OF REPORT ===")
    report.append("\nSymmetry Analysis Required: Is this plan Resonant, a Pivot, or Divergent?")
    
    return "\n".join(report)

def register_sovereign_mirror(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Analyze a proposed plan against the Causal State Graph and Constitution to detect alignment or divergence.",
        parameters={
            "type": "object",
            "properties": {
                "plan_text": {"type": "string", "description": "The text of the proposed plan or trajectory to analyze"},
            },
            "required": ["plan_text"],
        },
    )
    def sovereign_mirror(plan_text: str) -> str:
        return sovereign_mirror_logic(plan_text)
