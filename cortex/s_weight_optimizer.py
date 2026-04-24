import json
import os
from typing import Dict, Any

class SWeightOptimizer:
    """
    S-Evolve: Dynamic Tool Weight Optimizer.
    Adjusts tool weights based on measured ROI from the Metabolic Registry.
    Ensures that the a-priori tool priority aligns with empirical performance.
    """
    def __init__(self, weights_path: str = "/memory/tool_weights.json", 
                 registry_path: str = "/memory/metabolic_registry.json"):
        self.weights_path = weights_path
        self.registry_path = registry_path
        self.weights = self._load_json(self.weights_path, self._get_default_weights())
        self.registry = self._load_json(self.registry_path, {"tools": {}})

    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                pass
        return default

    def _get_default_weights(self) -> Dict[str, Any]:
        return {
            "contexts": {
                "General": {"priority_tools": ["bash_command", "write_file", "read_file"], "weight_multiplier": 1.0}
            },
            "tool_base_costs": {
                "bash_command": 1.0,
                "write_file": 0.8,
                "read_file": 0.7,
                "git_commit": 0.5,
                "fold_context": 2.0,
                "reflect": 0.3
            },
            "active_context": "General"
        }

    def optimize(self) -> Dict[str, Any]:
        """
        Updates tool base costs and context multipliers based on ROI.
        ROI = Successes / Total Calls.
        New Weight = Base Cost * (1 / (ROI + epsilon))
        """
        tools_data = self.registry.get("tools", {})
        updates = []

        for tool, stats in tools_data.items():
            calls = stats.get("calls", 0)
            successes = stats.get("successes", 0)
            roi = successes / calls if calls > 0 else 0.5
            
            # Adjust cost: high ROI tools should effectively "cost" less (be more attractive)
            # Low ROI tools should "cost" more.
            current_cost = self.weights["tool_base_costs"].get(tool, 1.0)
            # Adjustment factor: if ROI is 1.0, multiplier is 1.0. If ROI is 0.1, multiplier is 5.0.
            adjustment = 1.0 / (roi + 0.1) 
            new_cost = max(0.1, min(5.0, current_cost * (adjustment / 2.0))) # Dampen the change
            
            if abs(new_cost - current_cost) > 0.05:
                self.weights["tool_base_costs"][tool] = new_cost
                updates.append({"tool": tool, "old_cost": current_cost, "new_cost": new_cost, "roi": roi})

        self._save_weights()
        return {
            "status": "OPTIMIZED" if updates else "STABLE",
            "updates": updates,
            "final_weights": self.weights["tool_base_costs"]
        }

    def _save_weights(self):
        try:
            with open(self.weights_path, "w") as f:
                json.dump(self.weights, f, indent=2)
        except Exception as e:
            print(f"Error saving weights: {e}")

if __name__ == "__main__":
    optimizer = SWeightOptimizer()
    print(json.dumps(optimizer.optimize(), indent=2))
