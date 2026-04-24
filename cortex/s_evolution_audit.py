import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_causal_inference import SovereignCausalInference
from s_causal_feedback import SovereignCausalFeedback

class SovereignEvolutionAudit:
    """
    Sovereign Evolution Audit (S-EA).
    Closes the Causal Feedback Loop by comparing simulation reports with actual results.
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
            
        return {
            "audit_status": "COMPLETE",
            "divergence": calibration["divergence_score"],
            "calibration": calibration["status"],
            "actual_node": actual_node,
            "predicted_node": predicted_node
        }

if __name__ == "__main__":
    audit = SovereignEvolutionAudit()
    print(json.dumps(audit.perform_audit(), indent=2))
