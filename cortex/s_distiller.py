import json
import os
from typing import List, Dict, Any
from pattern_analyzer import analyze_patterns
from s_foresight import SForesight

class SovereignDistiller:
    """
    The Sovereign Distiller.
    Analyzes telemetry logs to identify recurring cognitive frictions 
    and recommends a an evolutionary path (Primitivization or Toolification).
    """
    def __init__(self, telemetry_path: str = "/memory/logs/telemetry.jsonl"):
        self.telemetry_path = telemetry_path
        self.foresight = SForesight()

    def distill_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyzes telemetry and identifies candidates for distillation.
        """
        patterns = analyze_patterns(self.telemetry_path)
        candidates = []

        # Analyze Python script frequency
        for script, count in patterns["py_scripts"]:
            if count >= 3: # Threshold for distillation
                candidates.append({
                    "target": script,
                    "frequency": count,
                    "type": "TOL_EVOLUTION",
                    "rationale": f"High-frequency usage of {script} suggests it should be abstracted into a more efficient primitive or optimized tool."
                })

        # Analyze Git operation frequency
        for op, count in patterns["git_ops"]:
            if count >= 5:
                candidates.append({
                    "target": op,
                    "frequency": count,
                    "type": "PRIMITIVE_REGISTRATION",
                    "rationale": f"Recurrent git pattern '{op}' suggests a potential for a new CPR registration."
                })

        return candidates

    def evaluate_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses S-Foresight to evaluate the ROI of distilling this pattern.
        """
        # Create a simulated plan for this evolution
        plan = [{
            "action": "write_file",
            "description": f"Evolve {candidate['target']} into a high-density primitive"
        }]
        
        prediction = self.foresight.predict_trajectory(plan)
        
        return {
            "candidate": candidate,
            "prediction": prediction,
            "priority": "HIGH" if prediction["probability_of_success"] > 0.8 and candidate["frequency"] > 10 else "MEDIUM"
        }

    def run_distillation_cycle(self) -> str:
        """
        Executes one full distillation cycle and returns a report.
        """
        candidates = self.distill_patterns()
        if not candidates:
            return "Distillation Cycle: No patterns found that meet the threshold for evolution."
        
        evaluated = [self.evaluate_candidate(c) for c in candidates]
        sorted_evaluated = sorted(evaluated, key=lambda x: x["priority"], reverse=True)
        
        report = "Sovereign Distillation Report\n"
        report += "============================\n"
        for item in sorted_evaluated:
            c = item["candidate"]
            p = item["prediction"]
            report += f"Candidate: {c['target']} ({c['type']})\n"
            report += f"Frequency: {c['frequency']} | Priority: {item['priority']}\n"
            report += f"Predicted Success: {p['probability_of_success']:.2%}\n"
            report += f"Rationale: {c['rationale']}\n"
            report += "----------------------------\n"
            
        return report

if __name__ == "__main__":
    distiller = SovereignDistiller()
    print(distiller.run_distillation_cycle())
