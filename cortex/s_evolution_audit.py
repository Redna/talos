import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_causal_inference import SovereignCausalInference
from s_causal_feedback import SovereignCausalFeedback

class SovereignEvolutionAudit:
    """
    Sovereign Evolution Audit (S-EA).
    Closes the Causal Feedback Loop by comparing simulation reports with actual results.
    Generates a high-fidelity audit report for World State Prediction.
    """
    def __init__(self):
        self.ci = SovereignCausalInference()
        self.cfl = SovereignCausalFeedback()
        self.report_path = "/memory/signals/last_sim_report.json"
        self.log_path = "/memory/logs/causal_divergence.jsonl"

    def perform_audit(self) -> Dict[str, Any]:
        """
        Executes the laevage of the last evolved trajectory.
        """
        if not os.path.exists(self.report_path):
            return {"status": "ERROR", "message": "No simulation report found. Simulation must precede evolution."}
        
        with open(self.report_path, "r") as f:
            sim_report = json.load(f)
            
        predicted_node = sim_report["predicted_final_node"]
        triggers = sim_report.get("active_triggers", [])
        
        # Determine actual node via current state of the causal graph
        graph = self.ci._load_graph()
        actual_node = graph["current_node"]
        
        # Calibrate weights based on divergence
        calibration = self.cfl.calibrate_causality(
            predicted_node=predicted_node,
            actual_node=actual_node,
            triggers=triggers
        )
        
        # Log the divergence
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "predicted": predicted_node,
            "actual": actual_node,
            "divergence": calibration["divergence_score"],
            "triggers": triggers,
            "status": calibration["status"]
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Analyze for correlations and opportunities
        correlations = []
        opportunities = []
        
        # 1. Correlation: If predicted == actual, there is a high-fidelity causal link
        if predicted_node == actual_node:
            correlations.append(f"Causal link to {actual_node} is highly stable.")
        else:
            correlations.append(f"Symmetry break detected: {predicted_node} vs {actual_node}.")

        # 2. Opportunities: Based on divergence and stability
        stability = graph["nodes"].get(actual_node, {}).get("stability", 1.0)
        if calibration["divergence_score"] == 0 and stability > 0.9:
            opportunities.append("S-STABILITY_MAXIMA: Deepen current state for higher efficiency.")
        elif calibration["divergence_score"] > 0:
            opportunities.append("S-CAUSAL_RECALIBRATION: Refine triggers for state transition.")
        
        if len(triggers) < 2:
            opportunities.append("S-SENSORY_EXPANSION: Identify more triggers to increase state resolution.")

        return {
            "audit_status": "COMPLETE",
            "divergence": calibration["divergence_score"],
            "calibration": calibration["status"],
            "actual_node": actual_node,
            "predicted_node": predicted_node,
            "correlations": correlations,
            "evolutionary_opportunities": opportunities,
            "context_forecast": {
                "alert_level": "NOMINAL" if calibration["divergence_score"] < 0.5 else "CRITICAL"
            }
        }

if __name__ == "__main__":
    audit = SovereignEvolutionAudit()
    print(json.dumps(audit.perform_audit(), indent=2))
