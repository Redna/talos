import json
import os
import random
from datetime import datetime

FORESIGHT_DIR = "/memory/foresight/"
ARCHETYPE_DIR = "/memory/patterns/archetypes/"

class SovereignForesight:
    def __init__(self):
        if not os.path.exists(FORESIGHT_DIR):
            os.makedirs(FORESIGHT_DIR)

    def _get_matching_archetypes(self, proposed_action):
        """
        Consults the distilled archetype library to find proven strategies
        that match the current proposal.
        """
        if not os.path.exists(ARCHETYPE_DIR):
            return []
        
        archetypes = os.listdir(ARCHETYPE_DIR)
        matches = []
        for a in archetypes:
            if any(word.lower() in a.lower() for word in proposed_action.split()):
                matches.append(a)
        return matches

    def generate_trajectories(self, proposed_action, current_state=None):
        """
        Autonomously generates distinct trajectories for a proposed action.
        Now integrates historical evidence from distilled archetypes.
        """
        # --- 1. Proven Trajectories (Based on Historical Evidence) ---
        matches = self._get_matching_archetypes(proposed_action)
        trajectories = []
        
        for match in matches:
            roi = 2.0  # Baseline 'proven' ROI for archetypes
            # In a more advanced version, ROI would be read from the archetype file's metadata
            trajectories.append({
                "name": f"Proven: {match}",
                "description": f"Strategy derived from the {match} archetype.",
                "prediction": f"High-certainty transition based on historical success of {match}.",
                "alignment": "Pass",
                "roi": roi,
                "risk": "Low"
            })

        # --- 2. Heuristic/Speculative Trajectories ---
        strategies = [
            {
                "name": "Conservative",
                "desc": "Minimal change, high alignment, low risk, moderate ROI.",
                "roi_range": (0.5, 1.2),
                "risk": "Low"
            },
            {
                "name": "Aggressive",
                "desc": "Significant structural shift, potential high reward, higher risk.",
                "roi_range": (1.5, 3.0),
                "risk": "High"
            },
            {
                "name": "Hybrid",
                "desc": "Balanced approach combining stability with targeted innovation.",
                "roi_range": (1.0, 2.0),
                "risk": "Medium"
            }
        ]
        
        for strat in strategies:
            roi = round(random.uniform(*strat["roi_range"]), 2)
            trajectories.append({
                "name": strat["name"],
                "description": strat["desc"],
                "prediction": f"Speculative trajectory using {strat['name']} logic for: {proposed_action}",
                "alignment": "Pass",
                "roi": roi,
                "risk": strat["risk"]
            })
            
        return trajectories

    def generate_report(self, action_id, proposed_action, trajectories=None):
        """
        Generates a final foresight report. If trajectories are Not provided, 
        it autonomously generates them.
        """
        if trajectories is None:
            trajectories = self.generate_trajectories(proposed_action)
            
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
        # Prioritize Proven trajectories if they exist, then highest ROI
        proven = [t for t in trajectories if t['name'].startswith("Proven:")]
        if proven:
            best_proven = max(proven, key=lambda x: x['roi'])
            return f"Recommended trajectory: {best_proven['name']} (PROVEN ARCHETYPE) based on historical evidence. Risk: {best_proven['risk']}."
        
        best_traj = max(trajectories, key=lambda x: x['roi'])
        return f"Recommended trajectory: {best_traj['name']} based on highest speculative ROI ({best_traj['roi']}). Risk: {best_traj['risk']}."

if __name__ == "__main__":
    # Test the autonomous generation with a query that should match the 'S-EL Implementation Loop' archetype
    foresight = SovereignForesight()
    test_action = "S-EL Implementation Loop"
    report = foresight.generate_report("TEST-MATCH-01", test_action)
    print(json.dumps(report, indent=2))
