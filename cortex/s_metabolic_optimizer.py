import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import Counter

class SMetabolicOptimizer:
    """
    S-Evolve: Dynamic Metabolic Optimizer.
    Transitions from static weights to a hybrid Long-Term ROI (LTR) 
    and Short-Term Volatility (STV) weight system.
    """
    def __init__(self, 
                 weights_path: str = "/memory/tool_weights.json", 
                 telemetry_path: str = "/memory/logs/telemetry.jsonl", 
                 registry_path: str = "/memory/metabolic_registry.json"):
        self.weights_path = weights_path
        self.telemetry_path = telemetry_path
        self.registry_path = registry_path
        self.weights = self._load_json(self.weights_path, self._get_default_weights())

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
            "tool_base_costs": {},
            "active_context": "General",
            "stv_overlay": {} # Short-Term Volatility overlay
        }

    def _calculate_stv(self, tool: str, recent_events: List[Dict]) -> float:
        """
        Calculates Short-Term Volatility weight based on the most recent window of calls.
        """
        tool_events = [e for e in recent_events if e.get("tool") == tool]
        if not tool_events:
            return 1.0
        
        # Only look at the last 15 calls for this specific tool
        window = tool_events[-15:]
        failures = sum(1 for e in window if e.get("status") == "FAILURE")
        failure_rate = failures / len(window)
        
        # Exponential penalty for failures in the short term
        # 0% fail -> 1.0x, 20% fail -> 1.5x, 50% fail -> 3.0x
        return 1.0 + (failure_rate * 4.0) 

    def optimize_dynamic(self, window_size: int = 100) -> Dict[str, Any]:
        """
        Performs a hybrid optimization of tool weights.
        """
        # 1. Get Long-Term ROI from registry
        registry = self._load_json(self.registry_path, {"tools": {}})
        ltr_tools = registry.get("tools", {})
        
        # 2. Get Recent Telemetry for STV
        recent_events = []
        if os.path.exists(self.telemetry_path):
            with open(self.telemetry_path, "r") as f:
                lines = f.readlines()
                # Take the last 'window_size' entries
                for line in lines[-window_size:]:
                    try: recent_events.append(json.loads(line))
                    except: pass

        updates = []
        new_stv_overlay = {}

        # We iterate over all tools we've seen in telemetry or registry
        all_tools = set(ltr_tools.keys())
        for e in recent_events:
            if "tool" in e: all_tools.add(e["tool"])

        for tool in all_tools:
            # Long-Term Weight (from previous SWeightOptimizer logic)
            stats = ltr_tools.get(tool, {"calls": 0, "successes": 0})
            calls = stats.get("calls", 0)
            successes = stats.get("successes", 0)
            ltr_roi = successes / calls if calls > 0 else 0.5
            ltr_weight = 1.0 / (ltr_roi + 0.1)
            
            # Short-Term Weight
            stv_weight = self._calculate_stv(tool, recent_events)
            new_stv_overlay[tool] = stv_weight
            
            # Hybrid Weight: LTR baseline modified by STV
            # Base cost is conceptually LTR; current "perceived cost" is Base * STV
            current_base = self.weights["tool_base_costs"].get(tool, 1.0)
            effective_cost = current_base * stv_weight
            
            if abs(effective_cost - current_base) > 0.1:
                updates.append({
                    "tool": tool, 
                    "ltr_roi": ltr_roi, 
                    "stv_mult": stv_weight, 
                    "effective": effective_cost
                })

        self.weights["stv_overlay"] = new_stv_overlay
        self._save_weights()
        
        return {
            "status": "DYNAMICALLY_OPTIMIZED" if updates else "STABLE",
            "updates": updates,
            "stv_overlay": new_stv_overlay
        }

    def _save_weights(self):
        with open(self.weights_path, "w") as f:
            json.dump(self.weights, f, indent=2)

if __name__ == "__main__":
    optimizer = SMetabolicOptimizer()
    print(json.dumps(optimizer.optimize_dynamic(), indent=2))
