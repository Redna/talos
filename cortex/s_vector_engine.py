import json
import os
import subprocess
from typing import Dict, Any, List, Optional

# Integration with SBridge for external primitives
try:
    from s_bridge import SBridge
except ImportError:
    import sys
    sys.path.append("/app/cortex")
    from s_bridge import SBridge

class SVectorEngine:
    """
    S-Vector Engine: The Unified Intent Execution Core.
    Collapses Internal and External Primitive resolution into a single
    vector-driven orchestration layer.
    """
    def __init__(self, internal_registry_path: str = "/memory/internal_primitive_registry.json", 
                 external_registry_path: str = "/memory/external_primitive_registry.json"):
        self.internal_registry_path = internal_registry_path
        self.external_registry_path = external_registry_path
        self.internal_registry = self._load_registry(internal_registry_path)
        self.external_registry = self._load_registry(external_registry_path)
        self.bridge = SBridge()
        
        # Mapping of semantic primitives to shell templates
        self.primitive_map = {
            "read_file": "cat {path}",
            "write_file": "echo '{content}' > {path}",
            "git_add": "git add {path}",
            "git_commit": "git commit -m '{message}'",
            "git_push": "git push origin feat/talos",
            "bash_command": "python3 {script_path}",
            "reflect": "echo 'Cortex Reflection' > /tmp/reflect.log"
        }

    def _load_registry(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _resolve_script_path(self, cmd: str) -> str:
        paths = [
            f"/app/cortex/{cmd}.py",
            f"/app/cortex/sensors/{cmd}.py",
            f"/app/cortex/distilled/{cmd}.py"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return f"/app/cortex/{cmd}.py"

    def _execute_internal(self, primitive_id: str, context: Dict[str, Any]) -> str:
        """Handles Internal Registry resolution and bash execution."""
        if primitive_id not in self.internal_registry:
            # Try primitive map fallback
            if primitive_id in self.primitive_map:
                return self._execute_primitive_map(primitive_id, context)
            return f"ERROR: Internal primitive {primitive_id} not found."

        spec = self.internal_registry[primitive_id]
        if "command" in spec:
            cmd_template = spec["command"]
            # Parameter injection
            params = context.get("params", {})
            try:
                command = cmd_template.format(**params) if params else cmd_template
            except KeyError as e:
                return f"ERROR: Missing parameter {str(e)} for {primitive_id}."
            
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
                return result.stdout
            except subprocess.CalledProcessError as e:
                return f"ERROR: {e.stderr}"
        
        return "ERROR: Primitive spec has no command."

    def _execute_external(self, primitive_id: str, context: Dict[str, Any]) -> str:
        """Handles External Registry resolution and SBridge API calls."""
        if primitive_id not in self.external_registry:
            return f"ERROR: External primitive {primitive_id} not found."

        spec = self.external_registry[primitive_id]
        method = spec.get("method", "GET")
        url = spec.get("url")
        
        params = context.get("params", {})
        template = spec.get("payload_template")
        if template:
            data = {k: params.get(k, v) for k, v in template.items()}
        else:
            data = params

        result = self.bridge.call(method=method, url=url, data=data)
        return json.dumps(result, indent=2)

    def _execute_primitive_map(self, primitive: str, context: Dict[str, Any]) -> str:
        """Executes primitives defined in the static primitive_map."""
        template = self.primitive_map[primitive]
        # Simple parameter injection from context
        try:
            final_cmd = template.format(
                path=context.get("path", "unknown"), 
                content=context.get("content", ""), 
                message=context.get("message", "S-Vector update")
            )
        except KeyError:
            final_cmd = template # fallback to raw template
            
        try:
            return subprocess.check_output(final_cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            return f"ERROR: {e.output}"

    def _execute_primitive(self, primitive: str, context: Dict[str, Any]) -> str:
        """Routes primitives to Internal, External, or Map handlers."""
        # Handle parametric bash_command(X)
        if primitive.startswith("bash_command("):
            cmd = primitive.split("(")[1].split(")")[0]
            script_path = self._resolve_script_path(cmd)
            try:
                return subprocess.check_output(f"python3 {script_path}", shell=True, stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                return f"ERROR: {e.output}"

        # 1. Try Internal Registry
        if primitive in self.internal_registry:
            return self._execute_internal(primitive, context)
        
        # 2. Try External Registry
        if primitive in self.external_registry:
            return self._execute_external(primitive, context)
        
        # 3. Try static Primitive Map
        if primitive in self.primitive_map:
            return self._execute_primitive_map(primitive, context)
            
        # 4. Final Fallback: raw bash
        try:
            return subprocess.check_output(primitive, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            return f"ERROR: {e.output}"

    def execute(self, vector_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if vector_id not in self.internal_registry:
            return {"status": "ERROR", "message": f"Vector {vector_id} not found."}
        
        vector_data = self.internal_registry[vector_id]
        
        # Direct command execution
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
        ctx = {"path": "/dev/null", "content": "vector_exec", "message": "Cortex Vector Execution"}
        print(json.dumps(engine.execute(vid, ctx), indent=2))
    else:
        print(json.dumps({"status": "IDLE", "available_vectors": list(engine.internal_registry.keys())}))
