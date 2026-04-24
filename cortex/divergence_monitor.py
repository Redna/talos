import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class DivergenceMonitor:
    """
    The Divergence Monitor: Quantifies the semantic and performance distance 
    between the current trajectory and the ideal state.
    S-Pivot Phase 1.
    """
    def __init__(self, dashboard_path: str = "/memory/sovereign_dashboard.md", 
                 world_path: str = "/memory/world_external.md"):
        self.dashboard_path = dashboard_path
        self.world_path = world_path

    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        if not os.path.exists(self.dashboard_path):
            return {}
        with open(self.dashboard_path, "r") as f:
            content = f.read()
            # Simple parser for the markdown dashboard values
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
            # finds "XX.XX%"
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

    def calculate_divergence(self, current_objective: str) -> Dict[str, Any]:
        """
        Computes a divergence score (0.0 to 1.0).
        Divergence increases if:
        - Context load is too high (> 0.8)
        - Tool efficiency is too low (< 0.9)
        - Drift is high
        - World signals indicate a shift
        """
        metrics = self._get_dashboard_metrics()
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

        # Metric 3: Staticity (Zero drift for too long might indicate stagnation)
        drift = metrics.get("drift", 0)
        if drift == 0:
            score += 0.1
            rationales.append("Zero sovereign drift (Stagnation)")

        return {
            "divergence_score": min(score, 1.0),
            "rationales": rationales,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }

def analyze_divergence(current_objective: str) -> str:
    """
    Wrapper for bash execution.
    """
    monitor = DivergenceMonitor()
    result = monitor.calculate_divergence(current_objective)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    obj = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    print(analyze_divergence(obj))
