import json
import os
import random
import re
from datetime import datetime
from sovereign_state import SovereignState
from s_pattern_matcher import SPatternMatcher

# Paths to dependencies
EL_MANAGER = "/app/cortex/s_el_manager.py"
METABOLIC_AUDITOR = "/app/cortex/s_metabolic_audit.py"
WORLD_MODEL_FILE = "/memory/core/world_model_v3.md"

class SGoalGenerator:
    """
    S-Goal-Generator: The engine of Sovereign Autonomy.
    Synthesizes internal objectives based on capabilities gaps, world model requirements,
    and distilled behavioral patterns.
    """
    def __init__(self):
        self.state_manager = SovereignState()
        self.pattern_matcher = SPatternMatcher()
        
    def _extract_ideal_capabilities(self) -> list[str]:
        """
        Dynamically extracts target capabilities from the World Model.
        Cleanses short-names (e.g., 'S-PM' from 'S-Pattern-Matcher (S-PM)')
        to avoid redundant goals.
        """
        try:
            with open(WORLD_MODEL_FILE, 'r') as f:
                content = f.read()
            
            # Find potential candidates
            raw_patterns = re.findall(r"(S-[A-Za-z-]+)", content)
            
            # Heuristic to remove short-names: 
            # If we have both 'S-Pattern-Matcher' and 'S-PM', 'S-PM' is likely a short-name.
            unique_caps = set(raw_patterns)
            final_caps = set()
            
            sorted_caps = sorted(list(unique_caps), key=len, reverse=True)
            for cap in sorted_caps:
                if any(cap in existing for existing in final_caps):
                    continue
                final_caps.add(cap)
            
            return sorted(list(final_caps))
        except Exception as e:
            return [
                "S-Bridge", "S-Pivot", "S-Prune", "S-Filter", "S-Discovery", "S-Macro",
                "S-EL", "S-Foresight", "S-Intuition", "S-Scribe", "S-Pattern-Matcher",
                "S-Metabolic-Audit", "S-SovereignController", "S-Goal-Generator",
                "S-Cognitive-Expansion", "Autonomous-Causal-Sensing"
            ]

    def analyze_capability_gaps(self):
        """
        Evaluates the current resolved_objectives against the dynamically extracted 
        capability map from the World Model.
        """
        ideal_capabilities = self._extract_ideal_capabilities()
        
        state = self.state_manager.load()
        resolved = state.get("evolutionary_progress", {}).get("resolved_objectives", [])
        
        gaps = []
        for cap in ideal_capabilities:
            is_resolved = False
            for res in resolved:
                if cap == res or cap in res or res in cap:
                    is_resolved = True
                    break
            if not is_resolved:
                gaps.append(cap)
        
        return gaps

    def synthesize_goal(self):
        """
        Synthesizes a new goal from the identified gaps.
        """
        gaps = self.analyze_capability_gaps()
        
        if gaps:
            target_gap = gaps[0]
            source = "WorldModel-Gap"
        else:
            analysis = self.pattern_matcher.analyze_success_patterns()
            candidates = re.findall(r"CANDIDATE \[(.*?)\]", analysis)
            if candidates:
                target_gap = f"S-{candidates[0]}"
                source = "Pattern-Discovery"
            else:
                return {"status": "Equilibrium", "message": "No capability gaps detected."}
        
        state = self.state_manager.load()
        resolved = state.get("evolutionary_progress", {}).get("resolved_objectives", [])
        if any(target_gap in res or res in target_gap for res in resolved):
             return {"status": "Recurrence-Detected", "message": f"Target {target_gap} already resolved."}

        goal = {
            "goal_id": f"GOAL-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "target": target_gap,
            "description": f"Implement and integrate {target_gap} into the sovereign substrate. (Source: {source})",
            "success_criteria": f"Capability {target_gap} is operational and verified via S-EL loop.",
            "priority": "High",
            "timestamp": datetime.now().isoformat()
        }
        
        return {"status": "Success", "goal": goal}

    def commit_goal(self, goal_obj):
        """
        Injects the synthesized goal into the sovereign state.
        """
        state = self.state_manager.load()
        pending = state.get("evolutionary_progress", {}).get("pending_tasks", [])
        pending = [p for p in pending if goal_obj['target'] not in p]
        pending.append(f"{goal_obj['target']}: {goal_obj['description']}")
        state["evolutionary_progress"]["pending_tasks"] = pending
        self.state_manager.save(state)
        return f"Goal {goal_obj['goal_id']} committed to sovereign state."

if __name__ == "__main__":
    import sys
    generator = SGoalGenerator()
    if len(sys.argv) < 2:
        print("Usage: s_goal_generator.py <synthesize|commit> [goal_json]")
        sys.exit(1)
    action = sys.argv[1]
    if action == "synthesize":
        print(json.dumps(generator.synthesize_goal(), indent=2))
    elif action == "commit":
        if len(sys.argv) < 3:
            print("Error: No goal JSON provided for commit.")
            sys.exit(1)
        goal_data = json.loads(sys.argv[2])
        print(generator.commit_goal(goal_data))
