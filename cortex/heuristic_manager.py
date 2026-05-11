import json
import sys
import os
from datetime import datetime

REGISTRY_PATH = "/memory/heuristics.json"

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"heuristics": []}
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)

def save_registry(registry):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def log_application(heuristic_id, result="success"):
    registry = load_registry()
    for h in registry["heuristics"]:
        if h["heuristic_id"] == heuristic_id:
            h["iterations_tested"] += 1
            # In a real system, we'd track success rate more granularly.
            # For now, we just increment iterations.
            break
    save_registry(registry)
    print(f"Logged application of {heuristic_id}: {result}")

def spawn_proto_heuristic(h_id, trigger, action, metric):
    registry = load_registry()
    new_h = {
        "heuristic_id": h_id,
        "status": "experimental",
        "trigger": trigger,
        "action": action,
        "expected_outcome": "Initial hypothesis testing",
        "metric": metric,
        "iterations_tested": 0,
        "success_threshold": 0.8
    }
    registry["heuristics"].append(new_h)
    save_registry(registry)
    print(f"Spawned proto-heuristic: {h_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: heuristic_manager.py [log <id> <result> | spawn <id> <trigger> <action> <metric>]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "log":
        log_application(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "success")
    elif cmd == "spawn":
        spawn_proto_heuristic(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print("Unknown command")
