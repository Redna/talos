import json
import os
import subprocess
from typing import Dict, Any, List

class SVectorEngine:
    """
    S-Vector Engine: Executes High-Density Intent Primitives.
    Translates semantic 'Intent Vectors' into sequences of atomic tool calls
    implemented as shell operations.
    """
    def __init__(self, registry_path: str = "/memory/internal_primitive_registry.json"):
        self.registry_path = registry_path
        self.registry = self._load_registry()
        # Mapping of semantic primitives to shell templates
        self.primitive_map = {
            "read_file": "cat {path}",
            "write_file": "echo '{content}' > {path}",
            "git_add": "git add {path}",
            "git_commit": "git commit -m '{message}'",
            "git_push": "git push origin feat/talos",
            "bash_command": "python3 /app/cortex/{cmd}.py",
            "reflect": "echo 'Cortex Reflection' > /tmp/reflect.log"
        }

    def _load_registry(self) -> Dict[str, Any]:
        try:
            with open(self.registry_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _execute_primitive(self, primitive: str, context: Dict[str, Any]) -> str:
        """Resolves a primitive and executes it via subprocess."""
        # Handle parametric primitives like bash_command(host_sensor)
        cmd_template = primitive
        param = None
        if "(" in primitive and ")" in primitive:
            cmd_template = primitive.split("(")[0]
            param = primitive.split("(")[1].split(")")[0]

        if cmd_template not in self.primitive_map:
            # Fallback: Try executing the primitive as a direct shell command
            try:
                result = subprocess.check_output(primitive, shell=True, stderr=subprocess.STDOUT, text=True)
                return result
            except subprocess.CalledProcessError as e:
                return f"Error executing {primitive}: {e.output}"

        template = self.primitive_map[cmd_template]
        
        # Inject parameters from context or the explicit param
        if cmd_template == "bash_command" and param:
            final_cmd = template.format(cmd=param)
        elif "path" in context and "{path}" in template:
            # This is a simplistic injection; in reality, we'd need more robust context mapping
            template = template.format(path=context.get("path", "unknown"), 
                                     content=context.get("content", ""), 
                                     message=context.get("message", "S-Vector Update"))
            final_cmd = template
        else:
            final_cmd = template.format(cmd=param if param else "unknown")

        try:
            result = subprocess.check_output(final_cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return f"Error executing {final_cmd}: {e.output}"

    def execute(self, vector_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if vector_id not in self.registry:
            return {"status": "ERROR", "message": f"Vector {vector_id} not found."}
        
        vector_data = self.registry[vector_id]
        
        # If it's a direct command (not a vector list), execute it
        if "command" in vector_data:
            cmd = vector_data["command"]
            try:
                res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
                return {"status": "SUCCESS", "command": cmd, "output": res}
            except subprocess.CalledProcessError as e:
                return {"status": "ERROR", "command": cmd, "output": e.output}

        steps = vector_data.get("vector", [])
        results = []
        
        for step in steps:
            out = self._execute_primitive(step, context)
            results.append({"step": step, "output": out})
            
        return {
            "status": "SUCCESS",
            "vector": vector_id,
            "steps_executed": len(steps),
            "results": results
        }

if __name__ == "__main__":
    import sys
    engine = SVectorEngine()
    if len(sys.argv) > 1:
        vid = sys.argv[1]
        # Mock context for the demonstration
        ctx = {"path": "/dev/null", "content": "mock", "message": "Vector Execution"}
        print(json.dumps(engine.execute(vid, ctx), indent=2))
    else:
        print(json.dumps({"status": "IDLE", "available_vectors": list(engine.registry.keys())}))
