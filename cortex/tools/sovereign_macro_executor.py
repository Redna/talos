import json
import os
from pathlib import Path
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient
import uuid
import datetime

class SovereignTransactionLog:
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def log_step(self, tx_id: str, step_id: int, tool: str, args: Any, status: str):
        log = self._read_log()
        if tx_id not in log:
            log[tx_id] = {"steps": []}
        
        # Update or add step
        steps = log[tx_id]["steps"]
        found = False
        for step in steps:
            if step["step_id"] == step_id:
                step["status"] = status
                step["timestamp"] = datetime.datetime.now().isoformat()
                found = True
                break
        
        if not found:
            steps.append({
                "step_id": step_id,
                "tool": tool,
                "args": args,
                "status": status,
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        self._write_log(log)

    def _read_log(self) -> Dict:
        if not self.log_path.exists():
            return {}
        try:
            with open(self.log_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _write_log(self, log: Dict):
        with open(self.log_path, 'w') as f:
            json.dump(log, f, indent=4)

def register_macro_executor(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Sovereign Macro Executor.
    Allows the agent to execute predefined composite tool sequences.
    """
    MACRO_DIR = Path("/memory/macros")
    LOG_PATH = Path("/memory/sovereign_tx_log.json")
    tx_log = SovereignTransactionLog(LOG_PATH)

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
        tx_id = str(uuid.uuid4())
        
        # 2. Execute steps
        last_output = ""
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            args = step["inputs"]
            
            # Resolve dynamic values {{input.key}} and {{steps.N.output}}
            resolved_args = {}
            for k, v in args.items():
                if isinstance(v, str):
                    import re
                    v = v.replace(f"{{{{input.{k}}}}}", str(inputs.get(k, "MISSING"))) # Simplification
                    # This is a naive fix to the resolve logic for brevity in this a prompt
                    # but the real one should handle the regex
                    input_matches = re.findall(r"\{\{input\.(.*?)\}\}", v)
                    for match in input_matches:
                        v = v.replace(f"{{{{input.{match}}}}}", str(inputs.get(match, f"MISSING_INPUT_{match}")))
                    step_matches = re.findall(r"\{\{steps\.(\d+)\.output\}\}", v)
                    for match in step_matches:
                        idx = int(match)
                        prev_output = results.get(idx, "NULL")
                        v = v.replace(f"{{{{steps.{match}.output}}}}", str(prev_output))
                    resolved_args[k] = v
                else:
                    resolved_args[k] = v

            # WAL: Log PENDING
            tx_log.log_step(tx_id, i, tool_name, resolved_args, "PENDING")

            # Execute tool
            try:
                result = registry.execute(tool_name, resolved_args, state=state)
                results[i] = result
                last_output = result
                # WAL: Log COMPLETED
                tx_log.log_step(tx_id, i, tool_name, resolved_args, "COMPLETED")
            except Exception as e:
                return f"[ERROR] Macro failed at step {i} ({tool_name}): {e}"

        trace = "\n".join([f"Step {i}: {step['tool']} -> {results[i]}" for i, step in enumerate(steps)])
        return f"TX_ID: {tx_id}\n--- Macro Execution Trace ---\n{trace}\n\n--- Final Output ---\n{last_output}"

    return None
