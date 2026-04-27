import json
import os
import random
from typing import List, Dict, Any
from datetime import datetime
from s_orchestrator import SOrchestrator
from s_simulation_engine import SovereignSimulationEngine
from s_causal_inference import SovereignCausalInference
from s_cognitive_synthesizer import SCognitiveSynthesizer
from sovereign_state import SovereignState

class SStratPlanner:
    """
    S-STRAT-PLANNER: The Sovereign Strategic Planner.
    Generates and scores multi-step evolutionary trajectories to optimize ROI.
    """
    def __init__(self):
        self.orchestrator = SOrchestrator()
        self.sim_engine = SovereignSimulationEngine()
        self.sci = SovereignCausalInference()
        self.synthesizer = SCognitiveSynthesizer()
        self.state_manager = SovereignState()

    def _get_goal_description(self, goal_id: str) -> str:
        """
        Attempts to retrieve a goal description from the sovereign state.
        """
        state = self.state_manager.load()
        pending = state.get("evolutionary_progress", {}).get("pending_tasks", [])
        
        # This is a heuristic search for the goal_id in pending tasks
        # Since goal_id might be part of the task string or just the target.
        for task in pending:
            if goal_id in task:
                return task
        
        return goal_id  # Fallback to goal_id as description

    def _generate_candidates(self, description: str) -> List[List[str]]:
        """
        Dynamically generates candidate trajectories using the Cognitive Synthesizer.
        """
        # 1. Find relevant archetypes (patterns)
        context = self.synthesizer.synthesize_plan_context(description)
        
        # Extract archetype names from the "--- Archetype: filename.md ---" markers
        archetypes = []
        import re
        matches = re.findall(r"--- Archetype: (.*?) ---", context)
        for m in matches:
            # Convert "filename.md" to "S-Capability" format for simulation
            # e.g., "S-Sensing-Refine.md" -> "S-Sensing-Refine"
            name = m.replace(".md", "")
            archetypes.append(name)
        
        if not archetypes:
            # Fallback trajectories if no archetypes are matched
            return [
                ["S-Sensing-Refine", "S-Analysis-Deepen", "S-Synthesis-Optimize"],
                ["S-Sovereign-Audit", "S-Causal-Map", "S-Trajectory-Lock"]
            ]
        
        # 2. Generate permutations as candidate trajectories
        candidates = []
        
        # Strategy 1: Linear sequence of the first 3 matched archetypes
        candidates.append(archetypes[:3])
        
        # Strategy 2: Shuffled sequence of a random subset
        if len(archetypes) > 1:
            shuffled = archetypes[:]
            random.shuffle(shuffled)
            candidates.append(shuffled[:3])
        
        # Strategy 3: Focused sequence (first 2)
        if len(archetypes) >= 2:
            candidates.append(archetypes[:2])
        
        # Strategy 4: Single-step leap
        for arch in archetypes[:2]:
            candidates.append([arch])
            
        return candidates

    def generate_roadmap(self, goal_id: str) -> str:
        """
        Synthesizes a sequence of leaps to archive a specific goal.
        """
        # 1. Grounding & Context
        description = self._get_goal_description(goal_id)
        state_report = self.orchestrator.orchestrate_state()
        report_data = json.loads(state_report)
        
        # 2. Dynamic Trajectory Generation
        candidates = self._generate_candidates(description)
        
        best_trajectory = None
        max_total_roi = -1.0
        
        # Starting state for simulation (from S-ORCH telemetry)
        # We use a rich state including current patterns and metabolic data
        current_sim_state = {
            "version": report_data.get('telemetry', {}).get('version', '1.0'),
            "active_patterns": report_data.get('telemetry', {}).get('patterns', []),
            "cognitive_load": report_data.get('metabolic_analysis', {}).get('cognitive_load', 'Optimal'),
            "memory_count": report_data.get('telemetry', {}).get('memory', {}).get('file_count', 0)
        }

        for trajectory in candidates:
            total_roi = 0.0
            temp_state = current_sim_state.copy()
            trajectory_valid = True
            
            for leap in trajectory:
                # Simulate the leap
                sim_res = self.sim_engine.simulate_state_shift(temp_state, leap)
                
                # Weight the ROI by causal confidence
                causal_res = self.sci.forecast_trajectory(leap)
                confidence = 1.0 if causal_res.get('confidence') == "High" else 0.5 if causal_res.get('confidence') == "Low" else 0.7
                
                weighted_roi = sim_res['projected_roi'] * confidence
                total_roi += weighted_roi
                
                # Update state for next leap in trajectory
                temp_state = sim_res['projected_state']
                
                if sim_res['projected_roi'] < 0.8: # Failure threshold
                    trajectory_valid = False
                    break
                    
            if trajectory_valid and total_roi > max_total_roi:
                max_total_roi = total_roi
                best_trajectory = trajectory

        # 3. Final Synthesis
        roadmap = {
            "goal_id": goal_id,
            "description": description,
            "selected_trajectory": best_trajectory,
            "cumulative_roi": round(max_total_roi, 2) if best_trajectory else 0.0,
            "timestamp": datetime.now().isoformat(),
            "status": "Optimized" if best_trajectory else "Degraded",
            "grounding": {
                "initial_version": current_sim_state["version"],
                "initial_patterns": len(current_sim_state["active_patterns"])
            }
        }
        
        return json.dumps(roadmap, indent=2)

def s_generate_roadmap(goal_id: str) -> str:
    planner = SStratPlanner()
    return planner.generate_roadmap(goal_id)
