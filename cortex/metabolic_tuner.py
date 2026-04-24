import json
import os
from collections import Counter
from typing import Dict, List, Any, Tuple

class MetabolicTuner:
    """
    S-Evolve: Metabolic Tuner.
    Analyzes telemetry to identify tool efficiency and propose optimization weights.
    """
    def __init__(self, telemetry_path: str = "/memory/logs/telemetry.jsonl", 
                 pivot_path: str = "/memory/logs/pivot_history.jsonl"):
        self.telemetry_path = telemetry_path
        self.pivot_path = pivot_path

    def analyze_tool_roi(self) -> Dict[str, Any]:
        """
        Calculates the Return on Investment (ROI) for each tool.
        ROI = (Successful Pivot Triggers) / (Total Tool Calls)
        """
        tool_counts = Counter()
        pivot_counts = 0
        
        # Analyze total tool usage
        if os.path.exists(self.telemetry_path):
            with open(self.telemetry_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        tool = entry.get("tool")
                        if tool:
                            tool_counts[tool] += 1
                    except:
                        continue

        # Analyze pivot success (proxy for 'progress')
        if os.path.exists(self.pivot_path):
            with open(self.pivot_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("event") == "PIVOT_TRIGGERED":
                            pivot_counts += 1
                    except:
                        continue

        # Calculate basic efficiency metrics
        efficiency = {}
        for tool, count in tool_counts.items():
            # This is a simplified ROI. Real ROI would track which tools 
            # preceded a successful pivot.
            efficiency[tool] = {
                "calls": count,
                "relative_weight": count / sum(tool_counts.values()) if tool_counts else 0
            }

        return {
            "tool_efficiency": efficiency,
            "total_pivots": pivot_counts,
            "recommendation": "Optimize high-frequency / low-impact tools" if pivot_counts < 10 else "System stable"
        }

    def propose_mutation(self, analysis: Dict[str, Any]) -> str:
        """
        Proposes a code change based on metabolic analysis.
        """
        eff = analysis.get("tool_efficiency", {})
        if not eff:
            return "No data to propose mutation."

        # Find most used tool
        most_used = max(eff, key=lambda k: eff[k]["calls"])
        
        return f"Proposal: The tool '{most_used}' is the primary metabolic driver. Consider optimizing its internal logic or creating a specialized wrapper to reduce token overhead."

if __name__ == "__main__":
    tuner = MetabolicTuner()
    analysis = tuner.analyze_tool_roi()
    proposal = tuner.propose_mutation(analysis)
    print(json.dumps({"analysis": analysis, "proposal": proposal}, indent=2))
