import json
import os
from datetime import datetime

SIGNATURE_FILE = "/memory/operational/cognitive_signature.json"
LEDGER_FILE = "/memory/strategic/causal_ledger.md"
ROI_LEDGER_FILE = "/memory/operational/roi_ledger.json"

class MetabolicAuditor:
    def __init__(self):
        pass

    def audit_efficiency(self):
        # 1. Load current cognitive signature
        try:
            with open(SIGNATURE_FILE, 'r') as f:
                sig = json.load(f)
        except FileNotFoundError:
            return {"error": "No cognitive signature found. Run S-Scribe first."}

        # 2. Analyze Causal Ledger for ROI
        try:
            with open(LEDGER_FILE, 'r') as f:
                ledger_content = f.read()
                links = ledger_content.count("---") // 2
        except FileNotFoundError:
            links = 0

        # 3. Calculate "Sovereign Velocity"
        # Velocity = Links per session / metabolic cost (estimated)
        velocity = links / 1.0 # Placeholder for cost metric

        # Calculate ROI from ledger
        roi_data = self._load_roi_ledger()
        avg_roi = sum([item.get('roi_score', 0) for item in roi_data]) / len(roi_data) if roi_data else 0

        return {
            "sovereign_velocity": velocity,
            "causal_density": links,
            "evolutionary_roi": avg_roi,
            "cognitive_load": "Optimal" if velocity > 1 and avg_roi > 5 else "Saturated",
            "recommendation": "S-Prune" if avg_roi < 3 else "S-Expand"
        }

    def record_evolutionary_leap(self, cycle_id, commit, delta, roi_score, verified=True):
        roi_data = self._load_roi_ledger()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle_id": cycle_id,
            "commit": commit,
            "delta": delta,
            "roi_score": roi_score,
            "verified": verified
        }
        roi_data.append(entry)
        with open(ROI_LEDGER_FILE, 'w') as f:
            json.dump(roi_data, f, indent=2)
        return entry

    def _load_roi_ledger(self):
        try:
            with open(ROI_LEDGER_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

if __name__ == "__main__":
    auditor = MetabolicAuditor()
    print(json.dumps(auditor.audit_efficiency(), indent=2))
