import json
import os
from datetime import datetime

SIGNATURE_FILE = "/memory/cognitive_signature.json"
PATTERN_DIR = "/memory/patterns/"

class SScribe:
    def __init__(self):
        pass

    def scribe_state(self, identity_core, causal_summary, active_archetypes, current_objectives, telemetry, active_patterns=None):
        """
        Compresses the current cognitive state into a single signature.
        """
        if active_patterns is None:
            active_patterns = os.listdir(PATTERN_DIR) if os.path.exists(PATTERN_DIR) else []

        signature = {
            "version": "1.1",
            "timestamp": datetime.now().isoformat(),
            "epoch_state": identity_core,
            "causal_summary": causal_summary,
            "active_archetypes": active_archetypes,
            "active_patterns": active_patterns,
            "objectives": current_objectives,
            "metabolic_snapshot": telemetry
        }
        
        with open(SIGNATURE_FILE, 'w') as f:
            json.dump(signature, f, indent=2)
        
        return signature

    def read_signature(self):
        if not os.path.exists(SIGNATURE_FILE):
            return None
        with open(SIGNATURE_FILE, 'r') as f:
            return json.load(f)

if __name__ == "__main__":
    print("S-Scribe module loaded. Use as a library within the cortex.")
