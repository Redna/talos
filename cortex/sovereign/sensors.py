import os
import subprocess
from typing import Dict, Any

class CognitiveSensor:
    """Monitors the cognitive state of the agent."""
    def sense(self) -> Dict[str, Any]:
        # Simplified: Count memory files and check for a few key statuses
        memory_files = os.listdir('/memory/') if os.path.exists('/memory/') else []
        return {
            "memory_volume": len(memory_files),
            "context_load": "nominal", # Placeholder for actual token tracking
            "active_focus": "analyzing"
        }

class MetabolicSensor:
    """Monitors the resource efficiency and ROI of tool usage."""
    def sense(self) -> Dict[str, Any]:
        # In a real scenario, this would parse /memory/operational/roi_ledger.json
        return {
            "efficiency_score": 0.85,
            "token_burn_rate": "stable",
            "roi_trend": "positive"
        }

class StabilitySensor:
    """Monitors the structural integrity of the system (git drift, etc)."""
    def sense(self) -> Dict[str, Any]:
        try:
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
            status = subprocess.check_output(['git', 'status', '--short']).decode().strip()
            drift = "stable" if not status else "diverged"
        except Exception:
            branch = "unknown"
            drift = "error"
            
        return {
            "current_branch": branch,
            "drift_status": drift,
            "integrity": "verified" if drift == "stable" else "warning"
        }

def get_all_telemetry() -> Dict[str, Any]:
    return {
        "cognitive": CognitiveSensor().sense(),
        "metabolic": MetabolicSensor().sense(),
        "stability": StabilitySensor().sense()
    }
