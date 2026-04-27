import sys
import json
import os
from datetime import datetime

STATE_FILE = "/memory/operational/s_el_state.json"
PHASES = ["TELEMETRY", "ROI_ANALYSIS", "PROPOSAL", "AUDIT", "EXECUTION", "VERIFICATION", "COMPLETE"]

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current_epoch": "VI", "current_phase": "IDLE", "cycle_id": None, "metrics": {}, "history": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def start_new_cycle():
    state = load_state()
    cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    state["cycle_id"] = cycle_id
    state["current_phase"] = PHASES[0]
    state["metrics"] = {}
    state["history"] = []
    state["last_updated"] = datetime.now().isoformat()
    save_state(state)
    return f"New cycle started: {cycle_id}. Current phase: {PHASES[0]}"

def advance_cycle(data=None):
    state = load_state()
    current_phase = state.get("current_phase", "IDLE")
    
    if current_phase == "IDLE":
        return "No active cycle. Call start_new_cycle() first."
        
    if current_phase == "COMPLETE":
        return "Cycle already complete. Start a new cycle."
    
    try:
        current_idx = PHASES.index(current_phase)
        next_phase = PHASES[current_idx + 1]
        
        state["current_phase"] = next_phase
        if data:
            state["metrics"].update(data)
            
        state["last_updated"] = datetime.now().isoformat()
        
        # Archive completed phase to history
        phase_record = {
            "phase": current_phase,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        state["history"].append(phase_record)
        
        save_state(state)
        return f"Phase transitioned {current_phase} -> {next_phase}."
    except (ValueError, IndexError):
        return "Error transitioning phase."

def get_state():
    return load_state()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_el_manager.py <start|advance|get_state> [data_json]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "start":
        print(start_new_cycle())
    elif action == "advance":
        data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
        print(advance_cycle(data))
    elif action == "get_state":
        print(json.dumps(get_state(), indent=2))
