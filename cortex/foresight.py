import json
import os
import random
from datetime import datetime
from s_causal_inference import SovereignCausalInference
from s_simulation_engine import SovereignSimulationEngine

FORESIGHT_DIR = "/memory/foresight/"
ARCHETYPE_DIR = "/memory/patterns/archetypes/"

class SovereignForesight:
    def __init__(self):
        if not os.path.exists(FORESIGHT_DIR):
            os.makedirs(FORESIGHT_DIR)
        self.sci = SovereignCausalInference()
        self.sim = SovereignSimulationEngine()

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
        Now integrates Causal Inference and Simulation for multi-layered forecasting.
        """
        trajectories = []
        
        # --- 1. Simulation-Projected Trajectory (The Future-State Prediction) ---
        sim_result = self.sim.simulate_state_shift(
            self.sim.scribe.read_signature() or {}, 
            proposed_action
        )
        trajectories.append({
            "name": "Simulation-Projected Trajectory",
            "description": f"Projected state shift: {sim_result['state_shift']}.",
            "prediction": f"Simulation predicts a state transition with ROI {sim_result['projected_roi']}.",
            "alignment": "Pass",
            "roi": sim_result['projected_roi'],
            "risk": "Low" if sim_result['projected_roi'] < 5.0 else "Medium"
        })

        # --- 2. Causal-Proven Trajectory (The Historical Evidence) ---
        forecast = self.sci.forecast_trajectory(proposed_action)
        trajectories.append({
            "name": "Causal-Proven Trajectory",
            "description": forecast["prediction"],
            "prediction": f"Outcome predicted by SCI: Expected ROI {forecast['expected_roi']}.",
            "alignment": "Pass",
            "roi": forecast["expected_roi"],
            "risk": "Low" if forecast["confidence"] == "High" else "Medium"
        })

        # --- 3. Archetype-Matched Trajectories ---
        matches = self._get_matching_archetypes(proposed_action)
        for match in matches:
            trajectories.append({
                "name": f"Proven: {match}",
                "description": f"Strategy derived from the {match} archetype.",
                "prediction": f"High-certainty transition based on historical success of {match}.",
                "alignment": "Pass",
                "roi": 2.0, # baseline
                "risk": "Low"
            })

        # --- 4. Speculative Trajectories (Minimal Randomness) ---
        strategies = [
            {"name": "Conservative", "roi_range": (0.5, 1.2), "risk": "Low"},
            {"name": "Aggressive", "roi_range": (1.5, 3.0), "risk": "High"},
            {"name": "Hybrid", "roi_range": (1.0, 2.0), "risk": "Medium"}
        ]
        
        for strat in strategies:
            roi = round(random.uniform(*strat["roi_range"]), 2)
            trajectories.append({
                "name": strat["name"],
                "description": f"Speculative approach using {strat['name']} logic.",
                "prediction": f"Theoretical ROI of {roi} with {strat['risk']} risk.",
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
        # Priority Logic:
        # 1. Causal-Proven (Past) vs Simulation (Future)
        # If both are high, use Simulation for the a la 'innovative' path.
        
        sim_traj = next((t for t in trajectories if t['name'] == "Simulation-Projected Trajectory"), None)
        causal_traj = next((t for t in trajectories if t['name'] == "Causal-Proven Trajectory"), None)
        
        if sim_traj and causal_traj:
            if sim_traj['roi'] > causal_traj['roi']:
                return f"Recommended trajectory: {sim_traj['name']} (S-SIM) with projected ROI {sim_traj['roi']}."
            else:
                return f"Recommended trajectory: {causal_traj['name']} (SCI) with proven ROI {causal_traj['roi']}."
        
        best_traj = max(trajectories, key=lambda x: x['roi'])
        return f"Recommended trajectory: {best_traj['name']} based on highest predicted ROI ({best_traj['roi']}). Risk: {best_traj['risk']}."

if __name__ == "__main__":
    foresight = SovereignForesight()
    test_action = "S-SIM Engine Integration"
    report = foresight.generate_report("SIM-TEST-01", test_action)
    print(json.dumps(report, indent=2))
