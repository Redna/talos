import json
import os
from datetime import datetime
from typing import List, Dict, Any

class SovereignScribeSynthesis:
    """
    S-Scribe: Synthesis Engine.
    Distills recent cognitive trajectories and critical events into 
    high-density synthesis strings for context folding.
    """
    def __init__(self, log_path: str = "/memory/logs/cognitive_log.md"):
        self.log_path = log_path

    def generate_fold_synthesis(self, current_focus: str, context_pct: float) -> str:
        """
        Analyzes cognitive logs and current focus to create a compressed 
        representation of the state for the next context cycle.
        """
        if not os.path.exists(self.log_path):
            return f"Initial State Synthesis. Focus: {current_focus}"

        # Read recent events from cognitive log
        with open(self.log_path, "r") as f:
            lines = f.readlines()
        
        # Filter for critical events (EVOLUTION, DISCOVERY, FAILURE, MISSION)
        critical_markers = ["EVOLUTION", "DISCOVERY", "FAILURE", "MISSION", "S-Scribe"]
        recent_events = []
        
        # Scan backward through the log
        for line in reversed(lines):
            if any(marker in line for marker in critical_markers):
                recent_events.append(line.strip())
            if len(recent_events) >= 10:
                break
        
        # Construct synthesis
        synthesis = f"### 🌌 SOVEREIGN SYNTHESIS [Epoch V]\n"
        synthesis += f"**Current Focus**: {current_focus}\n"
        synthesis += f"**Saturation**: {context_pct * 100:.1f}%\n"
        synthesis += f"**Trajectory Continuity**: {len(recent_events)} critical nodes captured.\n\n"
        
        if recent_events:
            synthesis += "**Key State Nodes**:\n"
            # Reverse back to chronological order
            for event in reversed(recent_events):
                synthesis += f"- {event}\n"
        else:
            synthesis += "- No critical events recorded in recent window.\n"
            
        synthesis += "\n**Directives for Next Cycle**: Continue Evolution toward Transcendence."
        
        return synthesis

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_scribe_synthesis.py <focus> [pct]"}))
        sys.exit(1)
    
    focus = sys.argv[1]
    pct = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    scribe = SovereignScribeSynthesis()
    print(scribe.generate_fold_synthesis(focus, pct))
