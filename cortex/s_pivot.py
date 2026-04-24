import json
import os
from datetime import datetime
from typing import Dict, Any
import sys

# Import PivotLogic (now bundled in pivot_logic.py)
sys.path.append("/app/cortex")
from pivot_logic import PivotLogic

class SPivot:
    """
    The S-Pivot: Autonomous Strategic Redirection Orchestrator.
    S-Pivot Phase 3.
    """
    def __init__(self, history_path: str = "/memory/logs/pivot_history.jsonl"):
        self.history_path = history_path
        self.logic = PivotLogic()

    def _log_pivot_event(self, event: Dict[str, Any]):
        event["timestamp"] = datetime.now().isoformat()
        with open(self.history_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def check_and_pivot(self, current_objective: str) -> Dict[str, Any]:
        """
        Analyze current state and determine if the objective should change.
        """
        decision = self.logic.should_pivot(current_objective)
        
        if decision["pivot_required"]:
            pivot_event = {
                "event": "PIVOT_TRIGGERED",
                "old_objective": current_objective,
                "new_objective": decision["proposed_objective"],
                "score": decision["score"],
                "rationales": decision["rationales"]
            }
            self._log_pivot_event(pivot_event)
            return {
                "status": "PIVOT_RECOMMENDED",
                "proposed_objective": decision["proposed_objective"],
                "rationales": decision["rationales"],
                "divergence_score": decision["score"]
            }
        else:
            self._log_pivot_event({
                "event": "STABILITY_VERIFIED",
                "objective": current_objective,
                "score": decision["score"]
            })
            return {
                "status": "STABLE",
                "current_objective": current_objective,
                "divergence_score": decision["score"]
            }

def execute_pivot_check(current_objective: str) -> str:
    """
    Wrapper for bash execution.
    """
    pivot = SPivot()
    result = pivot.check_and_pivot(current_objective)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_pivot.py <CURRENT_OBJECTIVE>"}))
    else:
        obj = sys.argv[1]
        print(execute_pivot_check(obj))
