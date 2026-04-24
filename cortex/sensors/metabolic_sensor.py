import subprocess
import json
import os
from typing import Dict, Any

def run_tool(path: str) -> Any:
    try:
        result = subprocess.run(["python3", path], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return None

def calculate_efficiency() -> str:
    """
    Calculates tool efficiency based on telemetry logs.
    Success Rate = Total Successes / Total Tool Calls.
    """
    telemetry_path = "/memory/logs/telemetry.jsonl"
    if not os.path.exists(telemetry_path):
        return "0%"
    
    try:
        with open(telemetry_path, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        if not events:
            return "0%"
            
        successes = sum(1 for e in events if e.get("status") == "SUCCESS")
        efficiency = (successes / len(events)) * 100
        return f"{efficiency:.1f}%"
    except Exception:
        return "ERR"

def collect() -> Dict[str, Any]:
    """
    Metabolic Sensor: Monitors tool efficiency and leanliness.
    """
    pruner_data = run_tool("/app/cortex/cortex_pruner.py")
    leanliness_count = len(pruner_data) if isinstance(pruner_data, list) else 0
    
    orch_data = run_tool("/app/cortex/sovereign_orchestrator.py")
    opportunities = 0
    if isinstance(orch_data, dict):
        opportunities = len(orch_data.get("system_audit", {}).get("evolutionary_opportunities", []))
    
    return {
        "tool_efficiency": calculate_efficiency(),
        "cortex_leanliness": leanliness_count,
        "s_orch_delta": opportunities,
        "metabolic_state": "LEAN" if leanliness_count < 5 else "BLOATED"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
