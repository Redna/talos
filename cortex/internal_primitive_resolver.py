import json
import os
import subprocess
from typing import Dict, Any, Optional

class InternalPrimitiveResolver:
    """
    The Internal Primitive Resolver: Maps semantic Internal Primitives to 
    local system executions (bash patterns).
    Epoch V: Metabolic Distillation.
    """
    def __init__(self, registry_path: str = "/memory/internal_primitive_registry.json"):
        self.registry_path = registry_path
        self._registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if not os.path.exists(self.registry_path):
            return {}
        try:
            with open(self.registry_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading registry: {str(e)}")
            return {}

    def resolve_and_execute(self, primitive_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Resolves an internal primitive ID and executes the command on the host.
        """
        if primitive_id not in self._registry:
            return {"status": "ERROR", "message": f"Internal primitive {primitive_id} not found."}

        spec = self._registry[primitive_id]
        command_template = spec["command"]
        
        # Parameter injection
        if params:
            try:
                command = command_template.format(**params)
            except KeyError as e:
                return {"status": "ERROR", "message": f"Missing parameter for primitive {primitive_id}: {str(e)}"}
        else:
            command = command_template

        try:
            # Execute raw bash
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return {
                "primitive": primitive_id,
                "command": command,
                "stdout": result.stdout,
                "status": "SUCCESS"
            }
        except subprocess.CalledProcessError as e:
            return {
                "primitive": primitive_id,
                "command": command,
                "stderr": e.stderr,
                "status": "FAILURE"
            }

def execute_internal_primitive(primitive_id: str, params_json: Optional[str] = None) -> str:
    """
    Wrapper for bash execution.
    """
    resolver = InternalPrimitiveResolver()
    params = json.loads(params_json) if params_json else None
    result = resolver.resolve_and_execute(primitive_id, params)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: internal_primitive_resolver.py <PRIMITIVE_ID> [PARAMS_JSON]"}))
    else:
        p_id = sys.argv[1]
        p_params = sys.argv[2] if len(sys.argv) > 2 else None
        print(execute_internal_primitive(p_id, p_params))
