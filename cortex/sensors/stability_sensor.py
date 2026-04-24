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

def calculate_verify_rate() -> str:
    """
    Calculates S-VERIFY pass rate from verify logs.
    """
    verify_path = "/memory/logs/verify.jsonl"
    if not os.path.exists(verify_path):
        return "100%" # Default for fresh systems
    
    try:
        with open(verify_path, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        if not events:
            return "100%"
            
        passes = sum(1 for e in events if e.get("result") == "PASS")
        rate = (passes / len(events)) * 100
        return f"{rate:.1f}%"
    except Exception:
        return "ERR"

def collect() -> Dict[str, Any]:
    """
    Stability Sensor: Monitors PFM signatures and system drift.
    """
    sentinel_data = run_tool("/app/cortex/sentinel_scan.py")
    signatures = 0
    if isinstance(sentinel_data, dict):
        signatures = len(sentinel_data.get("findings", []))
    
    drift_data = subprocess.run(
        ["git", "log", "--since='24 hours ago'", "--oneline", "|", "wc", "-l"], 
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    
    try:
        commit_count = int(drift_data)
    except:
        commit_count = 0

    return {
        "pfm_signatures": signatures,
        "daily_drift_count": commit_count,
        "s_verify_pass_rate": calculate_verify_rate(),
        "stability_status": "STABLE" if signatures == 0 else "VOLATILE"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
