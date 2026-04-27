import json
import os
from datetime import datetime
from s_metabolic_audit import MetabolicAuditor

# Causal Mapping Paths
ROI_LEDGER_FILE = "/memory/operational/roi_ledger.json"
S_EL_STATE_FILE = "/memory/operational/s_el_state.json"

class SovereignCausalInference:
    def __init__(self):
        self.auditor = MetabolicAuditor()
        self.roi_ledger = self._load_roi_ledger()

    def _load_roi_ledger(self):
        try:
            with open(ROI_LEDGER_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def infer_causal_link(self, proposed_delta):
        """
        Analyzes historical ROI and identifies if a specific 
        technical delta has led to high ROI in the past.
        """
        high_roi_threshold = 5.0
        proven_links = []
        
        for entry in self.roi_ledger:
            if entry.get('roi_score', 0) >= high_roi_threshold:
                # Check for semantic overlap between proposal and successful historical delta
                if any(word.lower() in entry.get('delta', '').lower() for word in proposed_delta.split()):
                    proven_links.append({
                        "source_commit": entry.get('commit'),
                        "roi": entry.get('roi_score'),
                        "delta": entry.get('delta')
                    })
                
        return proven_links

    def forecast_trajectory(self, proposed_delta):
        """
        Synthesizes a prediction based on proven causal links.
        """
        links = self.infer_causal_link(proposed_delta)
        
        if links:
            # Calculate weighted average ROI of proven links
            avg_roi = sum([l['roi'] for l in links]) / len(links)
            return {
                "type": "Causal-Proven",
                "prediction": f"Trajectory predicted via {len(links)} historical causal matches.",
                "expected_roi": round(avg_roi, 2),
                "confidence": "High",
                "evidence": links
            }
        
        # Fallback to baseline a la S-Scribe logic
        return {
            "type": "S-Scribe-Baseline",
            "prediction": "No direct causal matches found. Applying baseline heuristic.",
            "expected_roi": 1.5,
            "confidence": "Low",
            "evidence": []
        }

if __name__ == "__main__":
    sci = SovereignCausalInference()
    print(json.dumps(sci.forecast_trajectory("S-EL loop integration"), indent=2))
