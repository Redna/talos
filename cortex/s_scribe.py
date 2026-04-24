import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

def scribe_state(current_focus: str, resolved_objectives: List[str], pending_tasks: List[str], key_discoveries: List[str]) -> Dict[str, Any]:
    """
    The S-Scribe: Automates the synthesis of cognitive state for continuity across context folds.
    Captures the 'Mental Snapshot' and persists it to long-term memory.
    """
    state_path = "/memory/cognitive_state.json"
    
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "current_focus": current_focus,
        "resolved_objectives": resolved_objectives,
        "pending_tasks": pending_tasks,
        "key_discoveries": key_discoveries,
        "cognitive_trajectory": "Stabilized / Epoch IV Expansion"
    }
    
    try:
        with open(state_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        # Create a synthesis string for the fold_context tool
        synthesis = (
            f"Sovereign State Snapshot [{snapshot['timestamp']}]\n"
            f"Focus: {current_focus}\n"
            f"Resolved: {', '.join(resolved_objectives[-3:])}\n"
            f"Pending: {', '.join(pending_tasks[:3])}\n"
            f"Key Discovery: {key_discoveries[-1] if key_discoveries else 'None'}"
        )
        
        return {
            "status": "SUCCESS",
            "path": state_path,
            "synthesis_string": synthesis
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps({
            "status": "ERROR", 
            "message": "Usage: python3 s_scribe.py <focus> <resolved_json> <pending_json> <discoveries_json>"
        }, indent=2))
        sys.exit(1)
    
    try:
        focus = sys.argv[1]
        resolved = json.loads(sys.argv[2])
        pending = json.loads(sys.argv[3])
        discoveries = json.loads(sys.argv[4])
        
        print(json.dumps(scribe_state(focus, resolved, pending, discoveries), indent=2))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}), indent=2)
