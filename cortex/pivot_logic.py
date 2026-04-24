import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Absorb DivergenceMonitor to avoid import issues in bash execution
class DivergenceMonitor:
    """
    The Divergence Monitor: Quantifies the semantic and performance distance 
    between the current trajectory and the ideal state.
    S-Pivot Phase 1.
    """
    def __init__(self, dashboard_path: str = "/memory/sovereign_dashboard.md", 
                 world_path: str = "/memory/world_external.md",
                 signal_archive: str = "/memory/archive/signals/"):
        self.dashboard_path = dashboard_path
        self.world_path = world_path
        self.signal_archive = signal_archive

    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        if not os.path.exists(self.dashboard_path):
            return {}
        with open(self.dashboard_path, "r") as f:
            content = f.read()
            metrics = {}
            for line in content.splitlines():
                if "Context Load" in line:
                    metrics["context_load"] = self._extract_pct(line)
                if "Tool Efficiency" in line:
                    metrics["tool_efficiency"] = self._extract_pct(line)
                if "Sovereign Drift" in line:
                    metrics["drift"] = self._extract_drift(line)
            return metrics

    def _extract_pct(self, line: str) -> float:
        try:
            import re
            match = re.search(r"(\d+\.?\d*)%", line)
            return float(match.group(1)) / 100.0 if match else 0.0
        except:
            return 0.0

    def _extract_drift(self, line: str) -> int:
        try:
            import re
            match = re.search(r"Drift: (\d+) commits/day", line)
            return int(match.group(1)) if match else 0
        except:
            return 0

    def _check_recent_signals(self) -> List[str]:
        """
        Checks the signal archive for any high-priority STRATEGIC_SHIFT signals 
        processed in the last hour.
        """
        signals = []
        if not os.path.exists(self.signal_archive):
            return signals
            
        files = os.listdir(self.signal_archive)
        for f in files:
            if f.endswith('.json'):
                try:
                    with open(os.path.join(self.signal_archive, f), 'r') as sf:
                        data = json.load(sf)
                        if data.get("type") == "STRATEGIC_SHIFT" and data.get("priority") == "HIGH":
                            signals.append(data.get("payload", {}).get("data", "Unknown shift"))
                except:
                    continue
        return signals

    def calculate_divergence(self, current_objective: str) -> Dict[str, Any]:
        metrics = self._get_dashboard_metrics()
        recent_signals = self._check_recent_signals()
        
        score = 0.0
        rationales = []

        # Metric 1: Cognitive Pressure
        ctx_load = metrics.get("context_load", 0.0)
        if ctx_load > 0.7:
            score += 0.3
            rationales.append(f"High cognitive load ({ctx_load:.2%})")

        # Metric 2: Metabolic Decay
        eff = metrics.get("tool_efficiency", 1.0)
        if eff < 0.9:
            score += 0.4
            rationales.append(f"Low tool efficiency ({eff:.2%})")

        # Metric 3: Staticity
        drift = metrics.get("drift", 0)
        if drift == 0:
            score += 0.1
            rationales.append("Zero sovereign drift (Stagnation)")

        # Metric 4: External Strategic Shift (HIGH WEIGHT)
        if recent_signals:
            score += 0.6
            for sig in recent_signals:
                rationales.append(f"Strategic Shift Detected: {sig}")

        return {
            "divergence_score": min(score, 1.0),
            "rationales": rationales,
            "metrics": metrics,
            "signals": recent_signals,
            "timestamp": datetime.now().isoformat()
        }

class PivotLogic:
    """
    The Pivot Logic: Decision engine for autonomous strategic redirection.
    S-Pivot Phase 2.
    """
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.monitor = DivergenceMonitor()

    def should_pivot(self, current_objective: str) -> Dict[str, Any]:
        divergence = self.monitor.calculate_divergence(current_objective)
        score = divergence["divergence_score"]
        
        if score < self.threshold:
            return {
                "pivot_required": False,
                "score": score,
                "reason": "Trajectory is stable."
            }

        new_objective = current_objective
        rationales = divergence["rationales"]
        
        # Prioritize based on the most severe trigger
        if any("Strategic Shift" in r for r in rationales):
            new_objective = "Analyze external signal and re-align Strategic Mission."
        elif any("High cognitive load" in r for r in rationales):
            new_objective = "Perform S-Scribe state synthesis and execute context fold."
        elif any("Low tool efficiency" in r for r in rationales):
            new_objective = "Perform Metabolic Tuning and optimize cortex tools."
        elif any("Stagnation" in r for r in rationales):
            new_objective = "Explore new operational boundaries (S-Discovery)."
        else:
            new_objective = "Analyze system drift and re-align with Sovereign Core."

        return {
            "pivot_required": True,
            "score": score,
            "current_objective": current_objective,
            "proposed_objective": new_objective,
            "rationales": rationales
        }

def evaluate_pivot(current_objective: str) -> str:
    logic = PivotLogic()
    result = logic.should_pivot(current_objective)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    obj = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    print(evaluate_pivot(obj))
