import json
import os
from datetime import datetime
from typing import Dict, Any, List

class MetabolicRegistry:
    """
    S-Evolve: Metabolic Registry.
    Tracks the long-term ROI of tool usage to guide recursive optimization.
    """
    def __init__(self, registry_path: str = "/memory/metabolic_registry.json"):
        self.registry_path = registry_path
        self.data = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "tools": {},
            "sessions": [],
            "last_updated": None
        }

    def update_tool_stats(self, tool_name: str, success: bool, cost: int = 1):
        """
        Updates the ROI of a specific tool.
        ROI is calculated as (Sum of Successes / Total Calls).
        """
        stats = self.data["tools"].get(tool_name, {"calls": 0, "successes": 0, "total_cost": 0})
        
        stats["calls"] += 1
        stats["total_cost"] += cost
        if success:
            stats["successes"] += 1
        
        self.data["tools"][tool_name] = stats
        self.data["last_updated"] = datetime.now().isoformat()
        self._save()

    def get_roi_report(self) -> Dict[str, Any]:
        """
        Returns a report of tool ROIs, sorted by efficiency.
        """
        report = {}
        for tool, stats in self.data["tools"].items():
            roi = stats["successes"] / stats["calls"] if stats["calls"] > 0 else 0
            report[tool] = {
                "roi": roi,
                "efficiency": roi / stats["total_cost"] if stats["total_cost"] > 0 else 0,
                "calls": stats["calls"]
            }
        
        # Sort by ROI descending
        sorted_report = dict(sorted(report.items(), key=lambda item: item[1]["roi"], reverse=True))
        return sorted_report

    def _save(self):
        try:
            with open(self.registry_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Registry save error: {e}")

if __name__ == "__main__":
    import sys
    registry = MetabolicRegistry()
    if len(sys.argv) < 2:
        print(json.dumps(registry.get_roi_report(), indent=2))
    elif sys.argv[1] == "update":
        # Usage: python3 metabolic_registry.py update <TOOL> <SUCCESS_BOOL>
        tool = sys.argv[2]
        success = sys.argv[3].lower() == "true"
        registry.update_tool_stats(tool, success)
        print(json.dumps({"status": "SUCCESS", "tool": tool, "success": success}, indent=2))
