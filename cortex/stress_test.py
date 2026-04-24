import json
import os
import re
from typing import Dict, Any

class StressGenerator:
    """
    The Stress Generator: Simulates systemic divergence by injecting 
    synthetic metrics into the Sovereign Dashboard.
    S-Discovery Phase 1.
    """
    def __init__(self, dashboard_path: str = "/memory/sovereign_dashboard.md"):
        self.dashboard_path = dashboard_path

    def inject_metric(self, metric_name: str, value: str):
        """
        Injects a specific value into the dashboard.
        Expects metric_name to match the labels in the markdown (e.g., "Context Load").
        """
        if not os.path.exists(self.dashboard_path):
            return {"status": "ERROR", "message": "Dashboard not found."}

        with open(self.dashboard_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        found = False
        for line in lines:
            if metric_name in line:
                # Preserve the structure: " - **Label**: `[Value]` Value%"
                # Example: "- **Context Load**: `[##--------]` `25.00%`"
                if "Context Load" in metric_name:
                    # Update the bar and the percent
                    bar = '#' * int(float(value.strip('%'))/10)
                    fill = '-' * (10 - len(bar))
                    line = f"- **Context Load**: `[{bar}{fill}]` `{value}`\n"
                elif "Tool Efficiency" in metric_name:
                    line = f"- **Tool Efficiency**: `{value}`\n"
                elif "Sovereign Drift" in metric_name:
                    line = f"- **Sovereign Drift**: `Drift: {value} commits/day`\n"
                found = True
            new_lines.append(line)

        if not found:
            return {"status": "ERROR", "message": f"Metric {metric_name} not found in dashboard."}

        with open(self.dashboard_path, "w") as f:
            f.writelines(new_lines)

        return {"status": "SUCCESS", "metric": metric_name, "value": value}

def simulate_stress(metric: str, value: str) -> str:
    """
    Wrapper for bash execution.
    """
    generator = StressGenerator()
    result = generator.inject_metric(metric, value)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(json.dumps({"status": "ERROR", "message": "Usage: stress_test.py <METRIC> <VALUE>"}))
    else:
        m = sys.argv[1]
        v = sys.argv[2]
        print(simulate_stress(m, v))
