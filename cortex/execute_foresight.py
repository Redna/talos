import sys
import json
import subprocess
from cortex.foresight import SovereignForesight

def run_foresight():
    if len(sys.argv) < 3:
        print("Usage: python3 execute_foresight.py <action_id> <action_description> <trajectories_json>")
        sys.exit(1)
    
    action_id = sys.argv[1]
    action_desc = sys.argv[2]
    trajectories = json.loads(sys.argv[3])
    
    sf = SovereignForesight()
    report = sf.generate_report(action_id, action_desc, trajectories)
    print(json.dumps(report, indent=2))
    
    # Automatically log to Causal Ledger
    rec = report["recommendation"]
    subprocess.run([
        "python3", "/app/cortex/causal_logger.py", 
        action_id, "Foresight Simulation", f"Implemented {rec}", "Automated foresight logging", "Closing the loop between foresight and causality."
    ])

if __name__ == "__main__":
    run_foresight()
