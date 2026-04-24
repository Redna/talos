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
    Stability Sensor: Monitors PFM signatures and system drift.
    """
    # Scan for PFM Signatures
    sentinel_data = run_tool("/app/cortex/sentinel_scan.py")
    signatures = 0
    if isinstance(sentinel_data, dict):
        signatures = len(sentinel_data.get("findings", []))
    
    # Check commit frequency for drift (last 24h)
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
        "stability_status": "STABLE" if signatures == 0 else "VOLATILE"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
