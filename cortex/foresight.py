import json
import os
from datetime import datetime

FORESIGHT_DIR = "/memory/foresight/"

class SovereignForesight:
    def __init__(self):
        if not os.path.exists(FORESIGHT_DIR):
            os.makedirs(FORESIGHT_DIR)

    def generate_report(self, action_id, proposed_action, trajectories):
        """
        trajectories: List of dicts containing {name: str, prediction: str, alignment: str, roi: float}
        """
        report = {
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "proposed_action": proposed_action,
            "trajectories": trajectories,
            "recommendation": self._analyze_trajectories(trajectories)
        }
        
        file_path = os.path.join(FORESIGHT_DIR, f"foresight_{action_id}.json")
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

    def _analyze_trajectories(self, trajectories):
        # Simple ROI-based selection
        best_traj = max(trajectories, key=lambda x: x['roi'])
        return f"Recommended trajectory: {best_traj['name']} based on highest Sovereign ROI ({best_traj['roi']})."

if __name__ == "__main__":
    print("SovereignForesight module loaded. Use as a library within the cortex.")
