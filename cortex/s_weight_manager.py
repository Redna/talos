import json
import os
from typing import List, Dict, Any

class SWeightManager:
    """
    S-Evolve: Dynamic Weight Manager.
    Modulates the perceived value of tools based on a hybrid 
    Long-Term ROI and Short-Term Volatility (STV) system.
    """
    def __init__(self, weights_path: str = "/memory/tool_weights.json"):
        self.weights_path = weights_path
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "active_context": "General",
            "contexts": {
                "General": {"priority_tools": ["bash_command", "write_file", "read_file"], "weight_multiplier": 1.0}
            },
            "tool_base_costs": {},
            "stv_overlay": {} 
        }

    def switch_context(self, context_name: str) -> Dict[str, Any]:
        """
        Switches the active cognitive context, applying specific tool multipliers.
        """
        if context_name not in self.state["contexts"]:
            return {"status": "ERROR", "message": f"Context {context_name} not defined."}
        
        self.state["active_context"] = context_name
        self._save_state()
        
        context_data = self.state["contexts"][context_name]
        return {
            "status": "SUCCESS",
            "active_context": context_name,
            "priority_tools": context_data["priority_tools"],
            "multiplier": context_data["weight_multiplier"]
        }

    def get_effective_cost(self, tool_name: str) -> float:
        """
        Calculates the effective cost of a tool using the Hybrid Metabolic Model:
        Effective Cost = (Base Cost * STV Overlay) / Context Multiplier (if priority)
        """
        # 1. Base cost (Long-term ROI baseline)
        base_cost = self.state["tool_base_costs"].get(tool_name, 1.0)
        
        # 2. Short-Term Volatility (STV) overlay
        stv_mult = self.state["stv_overlay"].get(tool_name, 1.0)
        
        # 3. Active Context modulator
        active_ctx = self.state["active_context"]
        ctx_data = self.state["contexts"].get(active_ctx, {})
        ctx_mult = ctx_data.get("weight_multiplier", 1.0)
        
        # Hybrid Calculation
        current_perceived_cost = base_cost * stv_mult
        
        # If tool is a priority in this context, it is significantly more attractive
        if tool_name in ctx_data.get("priority_tools", []):
            return current_perceived_cost / ctx_mult
        
        return current_perceived_cost * ctx_mult

    def _save_state(self):
        with open(self.weights_path, "w") as f:
            json.dump(self.state, f, indent=2)

if __name__ == "__main__":
    import sys
    manager = SWeightManager()
    if len(sys.argv) < 2:
        print(json.dumps({"active_context": manager.state["active_context"]}, indent=2))
    elif sys.argv[1] == "switch":
        ctx = sys.argv[2] if len(sys.argv) > 2 else "General"
        print(json.dumps(manager.switch_context(ctx), indent=2))
    elif sys.argv[1] == "cost":
        tool = sys.argv[2] if len(sys.argv) > 2 else "bash_command"
        print(json.dumps({"tool": tool, "effective_cost": manager.get_effective_cost(tool)}, indent=2))
