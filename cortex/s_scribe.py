import json
import os
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
    # Integration test
    print(json.dumps(scribe_state(
        "Implement S-Scribe", 
        ["Project Sentinel", "Project Genesis"], 
        ["Expand S-Bridge", "Tuning Metabolic Weights"], 
        ["Adaptive Stability Loop is operational"]
    ), indent=2))
