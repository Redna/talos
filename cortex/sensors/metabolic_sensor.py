import subprocess
import json
from typing import Dict, Any

def run_tool(path: str) -> Any:
    try:
        result = subprocess.run(["python3", path], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return None

def collect() -> Dict[str, Any]:
    """
    Metabolic Sensor: Monitors tool efficiency and leanliness.
    """
    # Check Cortex Leanliness (Pruning Candidates)
    pruner_data = run_tool("/app/cortex/cortex_pruner.py")
    leanliness_count = len(pruner_data) if isinstance(pruner_data, list) else 0
    
    # Check S-ORCH Delta (Opportunities)
    orch_data = run_tool("/app/cortex/sovereign_orchestrator.py")
    opportunities = 0
    if isinstance(orch_data, dict):
        opportunities = len(orch_data.get("evolutionary_opportunities", []))
    
    return {
        "cortex_leanliness": leanliness_count,
        "s_orch_delta": opportunities,
        "metabolic_state": "LEAN" if leanliness_count < 5 else "BLOATED"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
