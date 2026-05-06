import json
import os
from pathlib import Path
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_macro_executor(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Sovereign Macro Executor.
    Allows the agent to execute predefined composite tool sequences.
    """
    MACRO_DIR = Path("/memory/macros")

    @registry.tool(
        description="Execute a pre-defined Sovereign Macro. Inputs are provided as a dictionary and resolved within the macro's steps.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the macro to execute"},
                "inputs": {"type": "object", "description": "Input parameters for the macro"},
            },
            "required": ["name", "inputs"]
        },
    )
    def execute_macro(name: str, inputs: Dict[str, Any]) -> str:
        # 1. Find macro definition
        # Search in root of MACRO_DIR or nested (e.g., state/)
        macro_file = None
        for p in MACRO_DIR.rglob(f"*{name}*.json"):
            if p.name == f"{name}.json":
                macro_file = p
                break
        
        if not macro_file:
            return f"[ERROR] Macro '{name}' not found in {MACRO_DIR}."

        with open(macro_file, 'r') as f:
            macro_def = json.load(f)

        steps = macro_def.get("steps", [])
        results = {}
        
        # 2. Execute steps
        last_output = ""
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            args = step["inputs"]
            
            # Resolve dynamic values {{input.key}} and {{steps.N.output}}
            resolved_args = {}
            for k, v in args.items():
                if isinstance(v, str):
                    # Resolve inputs
                    # Note: This is a simple substitution for demo purposes
                    # In a real system, this would use a proper templating engine
                    import re
                    
                    # {{input.key}}
                    input_matches = re.findall(r"\{\{input\.(.*?)\}\}", v)
                    for match in input_matches:
                        v = v.replace(f"{{{{input.{match}}}}}", str(inputs.get(match, f"MISSING_INPUT_{match}")))
                    
                    # {{steps.N.output}}
                    step_matches = re.findall(r"\{\{steps\.(\d+)\.output\}\}", v)
                    for match in step_matches:
                        idx = int(match)
                        prev_output = results.get(idx, "NULL")
                        v = v.replace(f"{{{{steps.{match}.output}}}}", str(prev_output))
                    
                    resolved_args[k] = v
                else:
                    resolved_args[k] = v

            # Execute tool
            try:
                # Use the registry to execute the tool
                result = registry.execute(tool_name, resolved_args, state=state)
                results[i] = result
                last_output = result
            except Exception as e:
                return f"[ERROR] Macro failed at step {i} ({tool_name}): {e}"

        trace = "\n".join([f"Step {i}: {step['tool']} -> {results[i]}" for i, step in enumerate(steps)])
        return f"--- Macro Execution Trace ---\n{trace}\n\n--- Final Output ---\n{last_output}"

    return None
