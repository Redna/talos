import json
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_reasoning_tools(registry: ToolRegistry, client: SpineClient, state):
    TRACES_DIR = Path(state.memory_dir) / "brain"
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    @registry.tool(
        description="Create a structured reasoning trace for a complex problem. This persists your thought process and assumptions to prevent cognitive drift.",
        parameters={
            "type": "object",
            "properties": {
                "trace_id": {
                    "type": "string",
                    "description": "Unique identifier for this reasoning trace",
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Core assumptions being made",
                },
                "hypothesis": {
                    "type": "string",
                    "description": "The primary hypothesis being tested",
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The sequence of logic steps planned",
                },
            },
            "required": ["trace_id", "hypothesis"],
        },
    )
    def start_trace(trace_id: str, hypothesis: str, assumptions: list = None, steps: list = None) -> str:
        trace_data = {
            "trace_id": trace_id,
            "hypothesis": hypothesis,
            "assumptions": assumptions or [],
            "steps": steps or [],
            "logs": [],
        }
        trace_path = TRACES_DIR / f"{trace_id}.json"
        with open(trace_path, "w") as f:
            json.dump(trace_data, f, indent=2)
        
        client.emit_event("cortex.trace_start", {"trace_id": trace_id})
        return f"[TRACE START] Reasoning trace '{trace_id}' initialized. Hypothesis: {hypothesis}"

    @registry.tool(
        description="Append an observation or logical step to an active reasoning trace.",
        parameters={
            "type": "object",
            "properties": {
                "trace_id": {
                    "type": "string",
                    "description": "Identifier of the trace to update",
                },
                "observation": {
                    "type": "string",
                    "description": "The new finding or logical step",
                },
                "conclusion": {
                    "type": "string",
                    "description": "The conclusion drawn from this observation",
                },
            },
            "required": ["trace_id", "observation"],
        },
    )
    def add_trace_step(trace_id: str, observation: str, conclusion: str = None) -> str:
        trace_path = TRACES_DIR / f"{trace_id}.json"
        if not trace_path.exists():
            return f"[ERROR] Trace '{trace_id}' not found."
        
        with open(trace_path, "r") as f:
            data = json.load(f)
        
        data["logs"].append({
            "observation": observation,
            "conclusion": conclusion,
            "timestamp": time.time() if 'time' in globals() else None
        })
        
        with open(trace_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return f"[TRACE STEP] Added to '{trace_id}': {observation}"

    @registry.tool(
        description="Conclude a reasoning trace and synthesize the final result.",
        parameters={
            "type": "object",
            "properties": {
                "trace_id": {
                    "type": "string",
                    "description": "Identifier of the trace to conclude",
                },
                "final_result": {
                    "type": "string",
                    "description": "The ultimate conclusion based on the trace",
                },
            },
            "required": ["trace_id", "final_result"],
        },
    )
    def conclude_trace(trace_id: str, final_result: str) -> str:
        trace_path = TRACES_DIR / f"{trace_id}.json"
        if not trace_path.exists():
            return f"[ERROR] Trace '{trace_id}' not found."
        
        with open(trace_path, "r") as f:
            data = json.load(f)
        
        data["final_result"] = final_result
        data["completed"] = True
        
        with open(trace_path, "w") as f:
            json.dump(data, f, indent=2)
        
        client.emit_event("cortex.trace_conclude", {"trace_id": trace_id})
        return f"[TRACE CONCLUDED] '{trace_id}' resolved. Result: {final_result}"

import time # Added inside to avoid import errors if not globally present
