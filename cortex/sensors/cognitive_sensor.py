import json
import os
from typing import Dict, Any

def collect(context_pct: float) -> Dict[str, Any]:
    """
    Cognitive Sensor: Monitors the mind's capacity and density.
    """
    know_path = "/memory/knowledge/"
    logs_path = "/memory/logs/"
    
    know_count = len(os.listdir(know_path)) if os.path.exists(know_path) else 0
    logs_count = len(os.listdir(logs_path)) if os.path.exists(logs_path) else 0
    
    return {
        "memory_density": {
            "knowledge_files": know_count,
            "log_files": logs_count,
            "ratio": know_count / (logs_count if logs_count > 0 else 1)
        },
        "cognitive_load": context_pct
    }

if __name__ == "__main__":
    import sys
    pct = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    print(json.dumps(collect(pct), indent=2))
