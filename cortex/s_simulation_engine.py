import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure the cortex directory is in the path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_causal_inference import SovereignCausalInference
from s_semantic_diff import SovereignSemanticDiff

class SovereignSimulationEngine:
    """
    Sovereign Simulation Engine v3 (S-SSE v3).
    Causal trajectory simulation now powered by Sovereign Causal Inference (S-CI).
    Moves from predictive heuristics to causal activation analysis.
    """
    def __init__(self, graph_path: str = "/memory/world_causal_graph.json"):
        self.ci_engine = SovereignCausalInference()
        self.diff_engine = SovereignSemanticDiff()
        self.report_path = "/memory/signals/last_sim_report.json"

    def simulate_trajectory(self, trajectory: List[Dict[str, Any]], current_pulse: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulates a sequence of actions by translating semantic shifts into causal triggers.
        """
        graph = self.ci_engine._load_graph()
        current_node = graph["current_node"]
        simulated_trajectory = []
        # Robust check for the nodes key and node stability
        cumulative_stability = graph.get("nodes", {}).get(current_node, {}).get("stability", 1.0)
        
        active_triggers = []
        
        for action in trajectory:
            semantic_impact = self._apply_action_and_extract_triggers(action, active_triggers)
            # CRITICAL: Use commit=False for simulation
            prediction = self.ci_engine.infer_transition(active_triggers, current_node, commit=False)
            
            stability_loss = 0.0
            if semantic_impact:
                complexity = semantic_impact.get("complexity_increase", 0.0)
                primary_shift = semantic_impact.get("primary_shift", "STABLE")
                shift_multiplier = 2.0 if primary_shift == "IDENTITY" else 1.0
                stability_loss = (complexity * 0.1) * shift_multiplier
            
            if prediction["transition"]:
                simulated_trajectory.append({
                    "action": action,
                    "transition": f"{prediction['from']} -> {prediction['to']}",
                    "score": prediction["score"],
                    "type": prediction["type"],
                    "triggers": prediction["triggers"]
                })
                current_node = prediction["to"]
                cumulative_stability *= (1.0 - stability_loss)
            else:
                simulated_trajectory.append({
                    "action": action,
                    "transition": "STEADY_STATE",
                    "score": 1.0,
                    "type": "STABLE",
                    "triggers": []
                })
                cumulative_stability *= (1.0 - (stability_loss * 0.5))
        
        risk_level = "LOW"
        if cumulative_stability < 0.7: risk_level = "MEDIUM"
        if cumulative_stability < 0.5: risk_level = "HIGH"
        
        recommendation = "PROCEED" if risk_level != "HIGH" else "S-PIVOT_REQUIRED"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "initial_node": graph["current_node"],
            "predicted_final_node": current_node,
            "simulated_path": simulated_trajectory,
            "final_stability": cumulative_stability,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "active_triggers": active_triggers
        }
        
        # Persist report for causal feedback
        with open(self.report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        return report

    def _apply_action_and_extract_triggers(self, action: Dict[str, Any], triggers: List[str]) -> Optional[Dict[str, Any]]:
        action_type = action.get("action")
        path = action.get("path", "")
        
        if action_type == "write_file":
            new_content = action.get("content", "")
            old_content = ""
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        old_content = f.read()
                except Exception:
                    old_content = ""
            
            diff_result = self.diff_engine.analyze_diff(old_content, new_content)
            primary_shift = diff_result["primary_shift"]
            
            trigger_map = {
                "SENSING": "SENSING_EXPANSION",
                "COGNITION": "S-WSP_EVOLUTION",
                "METABOLISM": "METABOLIC_OPTIMIZATION",
                "AGENCY": "AGENCY_EXPANSION",
                "IDENTITY": "IDENTITY_SHIFT"
            }
            
            if primary_shift in trigger_map:
                trigger = trigger_map[primary_shift]
                if trigger not in triggers:
                    triggers.append(trigger)
            
            return diff_result
            
        if action_type == "commit":
            if "Trajectory Stabilization" not in triggers:
                triggers.append("Trajectory Stabilization")
            return {"primary_shift": "STABLE", "complexity_increase": 0.0}
            
        return None

if __name__ == "__main__":
    sim = SovereignSimulationEngine()
    test_trajectory = [
        {"action": "write_file", "path": "/app/cortex/sensor_v2.py", "content": "def capture(): pass #sensing telemetry pulse"},
        {"action": "commit", "message": "adding sensing"}
    ]
    print(json.dumps(sim.simulate_trajectory(test_trajectory), indent=2))
