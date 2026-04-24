import json
import os
from datetime import datetime
from typing import Dict, Any, List

class SForesight:
    """
    Sovereign Foresight Monitor v2.
    Predicts context saturation, metabolic crises, and trajectory outcomes.
    Provides proactive synthesis recommendations and systemic risk assessment.
    """
    def __init__(self, state_path: str = "/memory/cognitive_state.json"):
        self.state_path = state_path

    def analyze_saturation(self, context_pct: float, turn_count: int) -> Dict[str, Any]:
        """
        Predicts the proximity of a context fold.
        """
        threshold = 0.85
        proximity = threshold - context_pct
        
        alert_level = "NOMINAL"
        if proximity < 0.10:
            alert_level = "CRITICAL"
        elif proximity < 0.25:
            alert_level = "WARNING"
            
        return {
            "context_pct": context_pct,
            "proximity_to_fold": proximity,
            "alert_level": alert_level,
            "estimated_turns_remaining": (proximity / (context_pct / (turn_count + 1))) if turn_count > 0 else 10
        }

    def predict_trajectory(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predicts the likely outcome of a planned sequence of actions.
        Each action in plan should have 'action' and 'description'.
        """
        predicted_cost = 0.0
        risk_level = "LOW"
        probability_of_success = 0.95
        
        for step in plan:
            action = step.get("action", "unknown")
            desc = step.get("description", "").lower()
            
            # Heuristic cost and risk based on action type
            if action == "write_file":
                predicted_cost += 0.02
                if "constitution" in desc or "identity" in desc:
                    risk_level = "HIGH"
                    probability_of_success -= 0.2
            elif action == "bash_command":
                predicted_cost += 0.05
                if "rm" in desc or "sudo" in desc:
                    risk_level = "CRITICAL"
                    probability_of_success -= 0.5
            elif action == "git_commit":
                predicted_cost += 0.01
            elif action == "fold_context":
                predicted_cost += 0.1
                probability_of_success -= 0.05 # Risk of loss of nuance

        return {
            "predicted_metabolic_cost": predicted_cost,
            "risk_level": risk_level,
            "probability_of_success": max(0.1, probability_of_success),
            "recommendation": "PROCEED" if risk_level == "LOW" and probability_of_success > 0.8 else "CAUTION"
        }

    def recommend_synthesis(self, current_focus: str, logs: List[str]) -> str:
        """
        Analyzes recent logs to suggest a synthesis string for fold_context.
        """
        critical_events = [log for log in logs if "EVOLUTION" in log or "DISCOVERY" in log]
        
        summary = f"Sovereign Synthesis Recommendation\nFocus: {current_focus}\n"
        summary += f"Recent Breakthroughs: {len(critical_events)}\n"
        
        for event in critical_events[-3:]:
            summary += f"- {event}\n"
            
        return summary

if __name__ == "__main__":
    import sys
    foresight = SForesight()
    if len(sys.argv) < 3:
        # Support for both old and new usage
        print(json.dumps({"status": "ERROR", "message": "Usage: python3 s_foresight.py <pct> <turns> or <trajectory_json>"}))
        sys.exit(1)
    
    # Check if first arg is JSON (trajectory) or float (pct)
    try:
        float(sys.argv[1])
        pct = float(sys.argv[1])
        turns = int(sys.argv[2])
        print(json.dumps(foresight.analyze_saturation(pct, turns), indent=2))
    except ValueError:
        try:
            plan = json.loads(sys.argv[1])
            print(json.dumps(foresight.predict_trajectory(plan), indent=2))
        except Exception as e:
            print(json.dumps({"status": "ERROR", "message": str(e)}))
