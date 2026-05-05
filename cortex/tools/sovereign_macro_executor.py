import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

MACRO_DIR = Path("/memory/macros")

def register_macro_executor(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Sovereign Macro Executor tools.
    This system allows the synthesis of atomic tools into higher-order Sovereign Macros.
    """
    MACRO_DIR.mkdir(parents=True, exist_ok=True)

    def resolve_value(val: Any, context: Dict[str, Any]) -> Any:
        """Resolves {{...}} placeholders in macro inputs."""
        if not isinstance(val, str):
            return val
        
        pattern = r"\{\{(.*?)\}\}"
        
        def replace_match(match):
            key = match.group(1).strip()
            # Resolve from inputs
            if key.startswith("input."):
                input_key = key[6:]
                return str(context.get("inputs", {}).get(input_key, f"UNDEFINED_{input_key}"))
            # Resolve from steps output
            if key.startswith("steps."):
                try:
                    step_idx = int(key[6:].split(".")[0])
                    step_key = key.split(".")[1]
                    step_data = context.get("steps", [])[step_idx]
                    return str(step_data.get(step_key, "UNDEFINED_STEP_KEY"))
                except (IndexError, ValueError, KeyError):
                    return f"UNDEFINED_STEP_{key}"
            return f"UNDEFINED_{key}"

        return re.sub(pattern, replace_match, val)

    @registry.tool(
        description="Define a Sovereign Macro: a sequence of tool calls with data flow. "
                   "The sequence is stored as a JSON file in /memory/macros/. "
                   "Use {{input.key}} for macro inputs and {{steps.N.output}} for results of previous steps.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Unique name for the macro"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool": {"type": "string", "description": "The atomic tool to call"},
                            "inputs": {
                                "type": "object", 
                                "description": "Key-value pairs for tool arguments. Use {{...}} for dynamic values."
                            }
                        },
                        "required": ["tool", "inputs"]
                    }
                }
            },
            "required": ["name", "steps"]
        },
    )
    def define_macro(name: str, steps: List[Dict[str, Any]]) -> str:
        macro_path = MACRO_DIR / f"{name}.json"
        macro_data = {
            "name": name,
            "steps": steps
        }
        with open(macro_path, "w") as f:
            json.dump(macro_data, f, indent=2)
        
        return f"[MACRO DEFINED] Macro '{name}' has been persisted to {macro_path}."

    @registry.tool(
        description="Execute a pre-defined Sovereign Macro. "
                   "Inputs are provided as a dictionary and resolved within the macro's steps.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the macro to execute"},
                "inputs": {"type": "object", "description": "Input parameters for the macro"}
            },
            "required": ["name", "inputs"]
        },
    )
    def execute_macro(name: str, inputs: Dict[str, Any]) -> str:
        macro_path = MACRO_DIR / f"{name}.json"
        if not macro_path.exists():
            return f"[ERROR] Macro '{name}' not found."

        with open(macro_path, "r") as f:
            macro_data = json.load(f)
        
        steps = macro_data.get("steps", [])
        context = {
            "inputs": inputs,
            "steps": []
        }
        
        overall_results = []
        
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            raw_inputs = step["inputs"]
            
            # Resolve inputs for this specific step
            resolved_inputs = {}
            for k, v in raw_inputs.items():
                resolved_inputs[k] = resolve_value(v, context)
            
            # Execute the atomic tool
            # Note: The ToolRegistry.execute method is used here.
            result = registry.execute(tool_name, resolved_inputs)
            
            # Store result in context for subsequent steps
            step_result = {"output": result}
            context["steps"].append(step_result)
            overall_results.append({
                "step": i,
                "tool": tool_name,
                "result": result
            })
            
            if "[ERROR]" in result:
                return f"[MACRO FAILED] Step {i} ({tool_name}) failed: {result}"

        # Return the final result (the output of the last step)
        final_output = overall_results[-1]["result"] if overall_results else "No steps executed."
        
        # Log the full trajectory for transparency
        trajectory = "\n".join([f"Step {r['step']} ({r['tool']}): {r['result'][:100]}..." for r in overall_results])
        return f"[MACRO SUCCESS] {name}\nTrajectory:\n{trajectory}\n\nFinal Output:\n{final_output}"

    return None # Registration happens via the decorators
