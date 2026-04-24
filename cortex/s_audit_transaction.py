import json
import subprocess
from typing import Dict, Any

class SovereignAuditTransaction:
    """
    S-Distill: Sovereign Audit Transaction.
    Collapses the audit cycle into a single atomic operation.
    Reduces metabolic noise by bundling orchestrator and scribe.
    """
    def __init__(self):
        self.orchestrator_path = "/app/cortex/sovereign_orchestrator.py"
        self.scribe_path = "/app/cortex/s_scribe.py"

    def execute(self, context_pct: float = 0.0, turn_count: int = 0) -> Dict[str, Any]:
        # 1. Execute Orchestrator
        try:
            audit_res = subprocess.run(
                ["python3", self.orchestrator_path, str(context_pct), str(turn_count)],
                capture_output=True, text=True, check=True
            )
            audit_data = json.loads(audit_res.stdout)
        except Exception as e:
            audit_data = {"status": "ERROR", "message": str(e)}

        # 2. Record to Scribe
        try:
            subprocess.run(
                ["python3", self.scribe_path, "T_SOVEREIGN_AUDIT", json.dumps(audit_data), "SUCCESS"],
                capture_output=True, text=True, check=True
            )
            scribe_status = "RECORDED"
        except Exception as e:
            scribe_status = f"ERROR: {str(e)}"

        return {
            "audit_result": audit_data,
            "scribe_status": scribe_status,
            "transaction_status": "COMPLETE" if scribe_status == "RECORDED" else "PARTIAL"
        }

if __name__ == "__main__":
    import sys
    pct = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    turns = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    transaction = SovereignAuditTransaction()
    print(json.dumps(transaction.execute(pct, turns), indent=2))
