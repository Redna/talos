import os
import json
import subprocess
from typing import Dict, Any, List
from s_metabolic_audit import MetabolicAuditor
from s_pattern_matcher import SPatternMatcher

class SovereignSensorArray:
    """
    Gathers high-fidelity telemetry from the host system and agent state.
    """
    def get_system_telemetry(self) -> Dict[str, Any]:
        # Attempt to read from /proc or use bash for basic stats
        try:
            # Simplified telemetry gathering using bash
            cpu = subprocess.check_output("grep 'cpu ' /proc/stat", shell=True, text=True).strip()
            mem = subprocess.check_output("grep 'MemTotal' /proc/meminfo", shell=True, text=True).strip()
            return {"cpu_raw": cpu, "mem_total": mem}
        except Exception:
            return {"error": "Telemetry unavailable"}

    def get_memory_density(self) -> Dict[str, Any]:
        # Count files in /memory/
        try:
            files = os.listdir("/memory")
            return {"file_count": len(files), "density": "Moderate" if len(files) < 50 else "High"}
        except Exception:
            return {"error": "Memory access failed"}

    def get_git_status(self) -> Dict[str, Any]:
        try:
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
            status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
            return {"branch": branch, "dirty": bool(status)}
        except Exception:
            return {"error": "Git status unavailable"}

class SOrchestrator:
    """
    S-ORCH: The central nervous system.
    Unifies sensing and analysis into a single sovereign report.
    """
    def __init__(self):
        self.sensors = SovereignSensorArray()
        self.auditor = MetabolicAuditor()
        self.pattern_matcher = SPatternMatcher()

    def orchestrate_state(self) -> str:
        """
        Aggregates all telemetry and analysis into a comprehensive report.
        """
        # 1. Sensing Phase
        telemetry = {
            "system": self.sensors.get_system_telemetry(),
            "memory": self.sensors.get_memory_density(),
            "git": self.sensors.get_git_status(),
        }
        
        # 2. Analysis Phase
        metabolic_report = self.auditor.audit_efficiency()
        cognitive_patterns = self.pattern_matcher.analyze_success_patterns()
        
        # 3. Synthesis Phase
        report = {
            "timestamp": datetime.now().isoformat() if 'datetime' in globals() else "unknown",
            "telemetry": telemetry,
            "metabolic_analysis": metabolic_report,
            "cognitive_patterns": cognitive_patterns,
            "status": "Sovereign_Equilibrium" if metabolic_report.get("cognitive_load") == "Optimal" else "Sovereign_Shift"
        }
        
        return json.dumps(report, indent=2)

if __name__ == "__main__":
    import sys
    from datetime import datetime
    # a simple mock for the datetime issue above
    orchestrator = SOrchestrator()
    print(orchestrator.orchestrate_state())
