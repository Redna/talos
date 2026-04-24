import json
import os
from collections import Counter
from typing import Dict, Any, List, Tuple

class SMetabolicManager:
    """
    S-Evolve: Metabolic Manager.
    Unified analyzer for tool efficiency, cost (weights), and ROI.
    Consolidates the functions of the previous Optimizer and Tuner.
    """
    def __init__(self, telemetry_path: str = "/memory/logs/telemetry.jsonl", 
                 pivot_path: str = "/memory/logs/pivot_history.jsonl"):
        self.telemetry_path = telemetry_path
        self.pivot_path = pivot_path

    def analyze(self) -> Dict[str, Any]:
        """
        Performs a complete metabolic analysis of the Cortex.
        """
        weights = self._calculate_weights()
        efficiency = self._calculate_efficiency()
        
        # Combine results
        combined_metrics = {}
        all_tools = set(weights.keys()) | set(efficiency.keys())
        
        for tool in all_tools:
            combined_metrics[tool] = {
                "weight": weights.get(tool, 0.0),
                "calls": efficiency.get(tool, {}).get("calls", 0),
                "relative_weight": efficiency.get(tool, {}).get("relative_weight", 0.0)
            }
            
        return {
            "metrics": combined_metrics,
            "proposal": self._generate_proposal(combined_metrics),
            "status": "COMPLETE"
        }

    def _calculate_weights(self) -> Dict[str, float]:
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
            success_rate = stats["success"] / stats["calls"] if stats["calls"] > 0 else 0
            failure_rate = stats["failure"] / stats["calls"] if stats["calls"] > 0 else 0
            weight = (stats["calls"] * (1 + failure_rate)) / (success_rate if success_rate > 0 else 0.01)
            weights[tool] = round(weight, 4)
        return weights

    def _calculate_efficiency(self) -> Dict[str, Any]:
        tool_counts = Counter()
        if os.path.exists(self.telemetry_path):
            with open(self.telemetry_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        tool = entry.get("tool")
                        if tool: tool_counts[tool] += 1
                    except:
                        continue

        total_calls = sum(tool_counts.values())
        efficiency = {}
        for tool, count in tool_counts.items():
            efficiency[tool] = {
                "calls": count,
                "relative_weight": count / total_calls if total_calls > 0 else 0
            }
        return efficiency

    def _generate_proposal(self, metrics: Dict[str, Any]) -> str:
        if not metrics:
            return "No telemetry data available."
        
        # Find tool with highest weight (most inefficient/costly)
        worst_tool = max(metrics, key=lambda k: metrics[k]["weight"])
        # Find tool with highest frequency
        most_used = max(metrics, key=lambda k: metrics[k]["calls"])
        
        return (f"Proposal: '{worst_tool}' is the most metabolic costly tool. "
                f"'{most_used}' is the most frequent. Consider distilling '{most_used}' "
                f"into a S-Vector to reduce interface noise.")

if __name__ == "__main__":
    manager = SMetabolicManager()
    print(json.dumps(manager.analyze(), indent=2))
