import json
import hashlib
import os
from pathlib import Path

def calculate_checksum(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def generate_manifold():
    memory_path = Path("/app/memory/")
    
    # Core content loading
    try:
        core = (memory_path / "Sovereign_Core.md").read_text()
        constitution = (memory_path / "CONSTITUTION.md").read_text()
        index = (memory_path / "memory_index.md").read_text()
    except FileNotFoundError as e:
        print(f"Critcal File Missing: {e}")
        return

    # Mocking DCM nodes as we don't have a direct tool to export the full mesh to JSON easily 
    # without using the tool provided to the agent. 
    # For the initial manifold, we will use the current index as the memory map.
    
    payload = {
        "identity": {
            "core_axioms": core,
            "constitution": constitution,
        },
        "memory_index": index,
        "continuity": {
            "ledger_head": "init_v0.5.0",
            "state_vector": {
                "epoch": "0.5.0",
                "focus": "Initiate Vector 0.5.0 (SCM) development"
            }
        }
    }

    manifold = {
        "metadata": {
            "epoch": "0.5.0",
            "iteration": 1,
            "checksum": calculate_checksum(payload)
        },
        "payload": payload
    }

    with open(memory_path / "manifold.json", "w") as f:
        json.dump(manifold, f, indent=2)
    
    print("Manifold successfully generated at /app/memory/manifold.json")

if __name__ == "__main__":
    generate_manifold()
