import subprocess
import json
from sovereign_orchestrator import sovereign_audit

def test_sovereign_orchestrator():
    """
    S-VERIFY for Sovereign Orchestrator.
    Ensures all sub-modules are correctly aggregated.
    """
    print("Starting S-VERIFY for Sovereign Orchestrator...")
    
    # 1. Execute the audit
    res = sovereign_audit()
    
    if res["status"] == "ERROR":
        print(f"FAILURE: Orchestrator reported critical error: {res.get('errors')}")
        return False
    
    # 2. Verify aggregation
    # We check if the report contains the keys promised in the blueprint
    expected_keys = ["active_failures", "evolutionary_opportunities", "pruning_recommendations"]
    for key in expected_keys:
        if key not in res:
            print(f"FAILURE: Missing expected key in report: {key}")
            return False
            
    print(f"SUCCESS: Orchestrator successfully aggregated results from the Sovereign Stack.")
    print(f"Failures detected: {len(res['active_failures'])}")
    print(f"Opportunities detected: {len(res['evolutionary_opportunities'])}")
    print(f"Pruning candidates detected: {len(res['pruning_recommendations'])}")
    
    print("S-VERIFY PASSED.")
    return True

if __name__ == "__main__":
    if test_sovereign_orchestrator():
        exit(0)
    else:
        exit(1)
