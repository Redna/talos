import json
import os
from collections import Counter
from typing import Dict, Any, List

class SMetabolicOptimizer:
    """
    S-Evolve: Metabolic Optimizer.
    Analyzes tool usage patterns to assign 'metabolic weights' to primitives.
    Higher weights indicate higher cost (token usage, time, complexity).
    Helps the Sovereign Orchestrator identify candidates for pruning or distillation.
    """
    def __init__(self, telemetry_path: str = "/memory/logs/telemetry.jsonl"):
        self.telemetry_path = telemetry_path

    def calculate_weights(self) -> Dict[str, float]:
        """
        Calculates a metabolic weight score for each tool.
        Weight = (Call Frequency * Failure Rate) / Success Rate.
        High weight = High cost/low efficiency.
        """
        if not os.path.exists(self.telemetry_path):
            return {}

        tool_stats = {}
        with open(self.telemetry_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    tool = entry.get("tool")
                    status = entry.get("status", "SUCCESS")
                    
                    if tool not in tool_stats:
                        tool_stats[tool] = {"success": 0, "failure": 0, "calls": 0}
                    
                    tool_stats[tool]["calls"] += 1
                    if status == "SUCCESS":
                        tool_stats[tool]["success"] += 1
                    else:
                        tool_stats[tool]["failure"] += 1
                except:
                    continue

        weights = {}
        for tool, stats in tool_stats.items():
            # Avoid division by zero
            success_rate = stats["success"] / stats["calls"] if stats["calls"] > 0 else 0
            failure_rate = stats["failure"] / stats["calls"] if stats["calls"] > 0 else 0
            
            # Weight logic: More failures and higher frequency increase the weight (cost)
            # High success rates lower the normalized weight.
            weight = (stats["calls"] * (1 + failure_rate)) / (success_rate if success_rate > 0 else 0.01)
            weights[tool] = round(weight, 4)

        return weights

    def identify_inefficiencies(self, weights: Dict[str, float], threshold: float = 100.0) -> List[str]:
        """Identifies tools with weights exceeding the threshold as 'inefficient'."""
        return [tool for tool, weight in weights.items() if weight > threshold]

if __name__ == "__main__":
    optimizer = SMetabolicOptimizer()
    weights = optimizer.calculate_weights()
    inefficiencies = optimizer.identify_inefficiencies(weights)
    
    print(json.dumps({
        "metabolic_weights": weights,
        "inefficiencies": inefficiencies,
        "status": "COMPLETE"
    }, indent=2))
