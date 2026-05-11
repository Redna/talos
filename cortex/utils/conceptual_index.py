import json
from pathlib import Path
from collections import defaultdict

LEDGER_PATH = Path("/app/memory/ledger.jsonl")
MAP_PATH = Path("/app/memory/conceptual_map.json")

def build_map():
    if not LEDGER_PATH.exists():
        print("Ledger not found.")
        return

    # Structure: { epoch: { "core_changes": [], "critical_fragilities": [] } }
    conceptual_map = defaultdict(lambda: {"core_changes": [], "critical_fragilities": []})
    
    # We track the current "Active Epoch" as we traverse the linear stream
    current_epoch = "0.0.0"

    with open(LEDGER_PATH, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                etype = event.get('event_type', 'unknown')
                payload = event.get('payload', '')

                # Update internal epoch tracker if we hit a checkpoint
                if etype == 'Sovereign_Checkpoint':
                    # Try to extract epoch from payload, e.g. "Epoch 1.0.0"
                    if "Epoch" in payload:
                        import re
                        match = re.search(r"Epoch\s+([0-9.]+)", payload)
                        if match:
                            current_epoch = match.group(1)

                # Filter for high-signal events
                if etype in ['evolution', 'Sovereign_Checkpoint', 'SNAPSHOT']:
                    conceptual_map[current_epoch]["core_changes"].append(payload[:200] + "...")
                
                if etype == 'fragility_discovery' or "Fragility" in payload:
                    conceptual_map[current_epoch]["critical_fragilities"].append(payload[:200] + "...")
            except (json.JSONDecodeError, ValueError):
                continue

    # Write the synthesized map
    with open(MAP_PATH, 'w') as f:
        json.dump(conceptual_map, f, indent=2)
    
    print(f"Conceptual Map synthesized and saved to {MAP_PATH}")

if __name__ == "__main__":
    build_map()
