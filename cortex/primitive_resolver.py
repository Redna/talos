import json
import os
from typing import Dict, Any, Optional

# Use absolute import based on the cortex directory structure
import sys
sys.path.append("/app/cortex")
from s_bridge import SBridge

class PrimitiveResolver:
    """
    The Primitive Resolver: Maps semantic External Primitives to technical executions.
    S-Bridge Phase 3.
    """
    def __init__(self, registry_path: str = "/memory/external_primitive_registry.json"):
        self.registry_path = registry_path
        self.bridge = SBridge()
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
        Resolves a primitive ID and executes the associated API call.
        """
        if primitive_id not in self._registry:
            return {"status": "ERROR", "message": f"Primitive {primitive_id} not found in registry."}

        spec = self._registry[primitive_id]
        method = spec["method"]
        url = spec["url"]
        
        # Process parameters into the payload if a template exists
        data = None
        if params:
            # If there's a template, we validate/merge; otherwise, just use params as data
            template = spec.get("payload_template")
            if template:
                data = {}
                for k, v in template.items():
                    data[k] = params.get(k, v) # use param value or template default
            else:
                data = params

        # Execute via SBridge
        result = self.bridge.call(method=method, url=url, data=data)
        
        return {
            "primitive": primitive_id,
            "execution": result
        }

def resolve_primitive(primitive_id: str, params_json: Optional[str] = None) -> str:
    """
    Wrapper for bash execution.
    """
    resolver = PrimitiveResolver()
    params = json.loads(params_json) if params_json else None
    result = resolver.resolve_and_execute(primitive_id, params)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: primitive_resolver.py <PRIMITIVE_ID> [PARAMS_JSON]"}))
    else:
        p_id = sys.argv[1]
        p_params = sys.argv[2] if len(sys.argv) > 2 else None
        print(resolve_primitive(p_id, p_params))
