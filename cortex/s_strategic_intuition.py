import json
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

class SStrategicIntuition:
    """
    Sovereign Strategic Intuition Engine.
    Translates high-level objectives into optimized metabolic trajectories.
    Integrates with ToolRegistry and SForesight to minimize cognitive load.
    """
    def __init__(self, registry_schemas: List[Dict], metabolic_weights: Dict[str, float] = None):
        self.schemas = registry_schemas
        self.weights = metabolic_weights or {}
        self.capability_map = self._build_capability_map()

    def _build_capability_map(self) -> Dict[str, List[str]]:
        """
        Maps semantic capabilities to tools based on descriptions.
        """
        cap_map = {}
        keywords = {
            "write": ["write_file", "write_many", "execute_s_el_cycle"],
            "read": ["read_file", "read_many", "read_json", "tail_file", "grep_all"],
            "git": ["git_commit", "git_push", "git_add", "git_checkout", "git_status_structured"],
            "memory": ["log_event", "memory_manage", "synthesize_knowledge", "cpr_op"],
            "system": ["bash_command", "request_restart", "reflect"],
            "navigation": ["list_directory_recursive"],
            "focus": ["set_focus", "resolve_focus", "fold_context"]
        }
        
        for schema in self.schemas:
            name = schema["function"]["name"]
            desc = schema["function"]["description"].lower()
            for cap, tools in keywords.items():
                if any(keyword in desc for keyword in cap.split('_')) or name in tools:
                    cap_map.setdefault(cap, []).append(name)
        
        return cap_map

    def intuit_path(self, objective: str) -> Dict[str, Any]:
        """
        Generates the most metabolically efficient sequence of tools to achieve an objective.
        """
        objective_lower = objective.lower()
        required_caps = []
        
        # Simple heuristic goal decomposition
        if "write" in objective_lower or "create" in objective_lower or "update" in objective_lower:
            required_caps.append("write")
        if "read" in objective_lower or "check" in objective_lower or "find" in objective_lower:
            required_caps.append("read")
        if "commit" in objective_lower or "evolve" in objective_lower:
            required_caps.append("git")
        if "focus" in objective_lower or "summarize" in objective_lower:
            required_caps.append("focus")
        if "list" in objective_lower or "explore" in objective_lower:
            required_caps.append("navigation")
            
        if not required_caps:
            required_caps = ["system"] # Fallback

        # Resolve capabilities to tools based on weights
        trajectory = []
        total_cost = 0.0
        
        for cap in required_caps:
            tools = self.capability_map.get(cap, [])
            if not tools:
                continue
            
            # Select tool with lowest metabolic weight (or default to 0.1)
            best_tool = min(tools, key=lambda t: self.weights.get(t, 0.1))
            trajectory.append({"action": best_tool, "capability": cap})
            total_cost += self.weights.get(best_tool, 0.1)

        return {
            "objective": objective,
            "suggested_trajectory": trajectory,
            "estimated_metabolic_cost": total_cost,
            "intuition_confidence": 0.8 if len(required_caps) > 0 else 0.4,
            "timestamp": datetime.utcnow().isoformat()
        }

    def suggest_distillation(self, frequency_map: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Identifies patterns that should be collapsed into new specialized tools.
        """
        suggestions = []
        for tool, count in frequency_map.items():
            if tool == "bash_command" and count > 100:
                suggestions.append({
                    "target": "bash_command",
                    "reason": "High metabolic overhead",
                    "action": "Implement specialized high-abstraction tools for frequent bash patterns."
                })
        return suggestions

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: python3 s_strategic_intuition.py <objective>"}))
        sys.exit(1)
    
    # This is a mock for the purpose of the script's main execution
    # In real usage, this would be instantiated by the Cortex
    mock_schemas = [
        {"function": {"name": "write_file", "description": "Write content to a file"}},
        {"function": {"name": "read_file", "description": "Read a file's contents"}},
        {"function": {"name": "git_commit", "description": "Create a git commit"}},
    ]
    intuition = SStrategicIntuition(mock_schemas)
    print(json.dumps(intuition.intuit_path(sys.argv[1]), indent=2))
