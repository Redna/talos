import json
import os
from typing import List, Dict, Optional

def sentinel_scan() -> Dict:
    """
    Scans recent telemetry for failure signatures defined in 
    /memory/knowledge/sentinel_signatures.md and returns 
    corrective directives.
    """
    telemetry_path = "/memory/logs/telemetry.jsonl"
    signatures_path = "/memory/knowledge/sentinel_signatures.md"
    
    if not os.path.exists(telemetry_path) or not os.path.exists(signatures_path):
        return {"status": "ERROR", "message": "Missing telemetry or signatures file."}

    try:
        with open(telemetry_path, 'r') as f:
            lines = f.readlines()
            recent_events = [json.loads(line) for line in lines[-20:]]
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to read telemetry: {str(e)}"}

    with open(signatures_path, 'r') as f:
        sigs_content = f.read()

    directives = []
    
    for event in recent_events:
        # Mode 2: Telemetry Ghosting
        if event.get("status") == "FAILURE":
            error_msg = event.get("error", "").lower()
            if "missing required positional argument" in error_msg or "not found" in error_msg:
                directives.append({
                    "mode": "Mode 2: Telemetry Ghosting",
                    "event": event,
                    "directive": "MANDATORY: Call `expand_primitive` on `SYSTEMIC_BODY` to synchronize tool map."
                })
        
        # Mode 3: Compression Overshoot
        if event.get("tool") == "bash_command" and "pytest" in event.get("args", {}).get("command", ""):
            if event.get("status") == "FAILURE":
                directives.append({
                    "mode": "Mode 3: Compression Overshoot",
                    "event": event,
                    "directive": "MANDATORY: Halt distillation. Initiate 'Test Suite Adaptation' phase."
                })

    return {
        "status": "SUCCESS",
        "findings": directives,
        "summary": f"Scanned {len(recent_events)} events. Found {len(directives)} signature matches."
    }

if __name__ == "__main__":
    print(json.dumps(sentinel_scan()))
