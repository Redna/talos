import json
import subprocess
from typing import Dict, List, Any

def run_script(script_path: str) -> Any:
    try:
        result = subprocess.run(
            ["python3", script_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def sovereign_audit_plus() -> Dict[str, Any]:
    """
    Extended Sovereign Orchestrator: Now includes Strategic Objective Synthesis.
    """
    # 1. Basic Sovereign Audit (S-ORCH)
    # We import the logic from the existing sovereign_orchestrator.py
    # but for the sake of this prototype, we'll just execute the script.
    audit_res = run_script("/app/cortex/sovereign_orchestrator.py")
    
    if isinstance(audit_res, dict) and audit_res.get("status") == "ERROR":
        return audit_res

    # 2. Strategic Objective Synthesis (SOS)
    # Pass the audit results to the SOS engine
    import sys
    import os
    sys.path.append("/app/cortex/")
    from sos_engine import synthesize_strategic_objective
    
    mission = synthesize_strategic_objective(audit_res)
    
    # 3. Merge report
    final_report = {
        "system_audit": audit_res,
        "strategic_mission": mission,
        "meta_status": "SOVEREIGN_ACTIVE"
    }
    
    return final_report

if __name__ == "__main__":
    print(json.dumps(sovereign_audit_plus(), indent=2))
