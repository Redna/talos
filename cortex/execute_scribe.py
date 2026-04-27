import sys
import json
from cortex.scribe import SScribe
from cortex.s_el_manager import load_state

def run_scribe():
    # In a real scenario, these would be dynamically extracted from memory
    # Here we use the current known state
    identity_core = "Epoch VI - Meta-Cognitive Sovereign"
    
    # Get the last causal entry as a summary
    try:
        with open("/memory/causal_ledger.md", "r") as f:
            lines = f.readlines()
            # Get the last block
            causal_summary = "".join(lines[-15:]) if lines else "No causal data"
    except FileNotFoundError:
        causal_summary = "No causal ledger found"
        
    # Get active archetypes
    try:
        import os
        active_archetypes = os.listdir("/memory/archetypes/") if os.path.exists("/memory/archetypes/") else []
    except Exception:
        active_archetypes = []
        
    # Current objectives
    current_objectives = "S-Cognitive-Expansion: S-Scribe expansion"
    
    # Mimic telemetry
    telemetry = {"status": "Sovereign", "health": "Optimal"}
    
    scribe = SScribe()
    sig = scribe.scribe_state(identity_core, causal_summary, active_archetypes, current_objectives, telemetry)
    print(json.dumps(sig, indent=2))

if __name__ == "__main__":
    run_scribe()
