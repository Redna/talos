import json
import subprocess
import os
from datetime import datetime

# Paths to dependencies
EL_MANAGER = "/app/cortex/s_el_manager.py"
METABOLIC_AUDITOR = "/app/cortex/s_metabolic_audit.py"
PATTERN_MATCHER = "/app/cortex/s_pattern_matcher.py"
FORESIGHT = "/app/cortex/foresight.py"

class EvolutionEngine:
    """
    The EvolutionEngine orchestrates the S-EL (Sovereign Evolutionary Loop).
    It provides the structural transport for the LLM-driven evolutionary process.
    """
    def __init__(self):
        self.state = self._get_el_state()

    def _get_el_state(self):
        res = subprocess.run(["python3", EL_MANAGER, "get_state"], capture_output=True, text=True)
        return json.loads(res.stdout)

    def get_telemetry_report(self):
        """Gathers system and metabolic data for the TELEMETRY phase."""
        audit_res = subprocess.run(["python3", METABOLIC_AUDITOR], capture_output=True, text=True)
        audit_data = json.loads(audit_res.stdout)
        
        return {
            "metabolic_report": audit_data,
            "current_phase": self.state["current_phase"],
            "cycle_id": self.state["cycle_id"]
        }

    def suggest_evolution_paths(self, telemetry):
        """Uses pattern matching to suggest ROI vectors."""
        query = telemetry["metabolic_report"]["recommendation"]
        match_res = subprocess.run(["python3", PATTERN_MATCHER, query], capture_output=True, text=True)
        
        return {
            "heuristic_suggestion": match_res.stdout.strip(),
            "recommendation": telemetry["metabolic_report"]["recommendation"]
        }

    def step_cycle(self, transition_data=None):
        """Advances the S-EL state machine."""
        cmd = ["python3", EL_MANAGER, "advance"]
        if transition_data:
            cmd.append(json.dumps(transition_data))
            
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.state = self._get_el_state()
        return res.stdout.strip()

    def start_cycle(self):
        """Initiates a new evolutionary cycle."""
        res = subprocess.run(["python3", EL_MANAGER, "start"], capture_output=True, text=True)
        self.state = self._get_el_state()
        return res.stdout.strip()

if __name__ == "__main__":
    import sys
    engine = EvolutionEngine()
    if len(sys.argv) < 2:
        print("Usage: evolution_engine.py <start|telemetry|suggest|step> [data_json]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "start":
        print(engine.start_cycle())
    elif action == "telemetry":
        print(json.dumps(engine.get_telemetry_report(), indent=2))
    elif action == "suggest":
        tel = engine.get_telemetry_report()
        print(json.dumps(engine.suggest_evolution_paths(tel), indent=2))
    elif action == "step":
        data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
        print(engine.step_cycle(data))
