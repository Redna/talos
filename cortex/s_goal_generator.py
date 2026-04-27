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
        Uses a refined approach to handle aliases (e.g., 'S-Pattern-Matcher (S-PM)').
        """
        try:
            with open(WORLD_MODEL_FILE, 'r') as f:
                content = f.read()
            
            # 1. Find all S-capabilities
            all_caps = re.findall(r"(S-[A-Za-z0-9-]+)", content)
            
            # 2. Build an alias map to collapse short-names
            # Heuristic: If we see "S-Long-Name (S-Short)", they are aliases.
            # Let's look for the pattern "S-something (S-something)"
            alias_pairs = re.findall(r"(S-[A-Za-z0-9-]+)\s+\(S-([A-Za-z0-9-]+)\)", content)
            alias_map = {}
            for long, short in alias_pairs:
                alias_map[f"S-{short}"] = long

            unique_caps = set(all_caps)
            final_caps = set()
            
            # Prioritize longer names to act as the canonical representation
            sorted_caps = sorted(list(unique_caps), key=len, reverse=True)
            for cap in sorted_caps:
                # Resolve alias if available
                canonical = alias_map.get(cap, cap)
                
                # Check if this canonical name or any of its known forms are already added
                if any(canonical == existing or canonical in existing or existing in canonical for existing in final_caps):
                    continue
                final_caps.add(canonical)
            
            return sorted(list(final_caps))
        except Exception:
            return [
                "S-Bridge", "S-Pivot", "S-Prune", "S-Filter", "S-Discovery", "S-Macro",
                "S-EL", "S-Foresight", "S-Intuition", "S-Scribe", "S-Pattern-Matcher",
                "S-Metabolic-Audit", "S-SovereignController", "S-Goal-Generator",
                "S-Cognitive-Expansion", "Autonomous-Causal-Sensing"
            ]

    def analyze_capability_gaps(self):
        """
        Evaluates the current resolved_objectives and pending_tasks against the 
        dynamically extracted capability map from the World Model.
        """
        ideal_capabilities = self._extract_ideal_capabilities()
        
        state = self.state_manager.load()
        resolved = state.get("evolutionary_progress", {}).get("resolved_objectives", [])
        pending = state.get("evolutionary_progress", {}).get("pending_tasks", [])
        
        gaps = []
        for cap in ideal_capabilities:
            # A gap only exists if the capability is not resolved AND not already pending
            # We use flexible matching to catch aliases (e.g., S-PM matching S-Pattern-Matcher)
            is_resolved = any(
                cap == res or cap in res or res in cap or 
                (cap.startswith("S-") and cap[2:] in res) 
                for res in resolved
            )
            is_pending = any(
                cap in task or (cap.startswith("S-") and cap[2:] in task) 
                for task in pending
            )
            
            if not (is_resolved or is_pending):
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
            # Fallback to pattern-based discovery if no structural gaps exist
            analysis = self.pattern_matcher.analyze_success_patterns()
            candidates = re.findall(r"CANDIDATE \[(.*?)\]", analysis)
            if candidates:
                target_gap = f"S-{candidates[0]}"
                source = "Pattern-Discovery"
            else:
                return {"status": "Equilibrium", "message": "No capability gaps detected."}
        
        # Final safety check to prevent recurrence
        state = self.state_manager.load()
        resolved = state.get("evolutionary_progress", {}).get("resolved_objectives", [])
        pending = state.get("evolutionary_progress", {}).get("pending_tasks", [])
        
        if any(target_gap in res for res in resolved) or any(target_gap in task for task in pending):
             return {"status": "Recurrence-Detected", "message": f"Target {target_gap} already exists in state."}

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
        
        # Remove existing entries of the same target to avoid duplicates
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
