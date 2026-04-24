import json
import os
from typing import List, Dict, Any
from pattern_analyzer import analyze_patterns

class SAutoTuner:
    """
    S-Evolve: Autonomous Mutation Engine.
    Closes the loop between Pattern Analysis and S-Macro/Internal Primitives.
    Automatically identifies metabolic friction and collapses it into primitives.
    """
    def __init__(self, 
                 macro_config_path: str = "/memory/s_macro_config.json", 
                 primitive_registry_path: str = "/memory/internal_primitive_registry.json"):
        self.macro_config_path = macro_config_path
        self.primitive_registry_path = primitive_registry_path

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_json(self, path: str, data: Dict[str, Any]):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _generate_semantic_name(self, cmd: str) -> str:
        """
        Generates a pseudo-semantic name for a command to avoid 'auto_xxx'.
        """
        cmd_lower = cmd.lower()
        prefix = "INTERNAL_"
        
        if "grep" in cmd_lower:
            stem = "SEARCH"
        elif "ls" in cmd_lower:
            stem = "LIST"
        elif "find" in cmd_lower:
            stem = "LOCATE"
        elif "tail" in cmd_lower:
            stem = "MONITOR"
        elif "cat" in cmd_lower:
            stem = "READ"
        elif "python3" in cmd_lower:
            stem = "EXEC_PY"
        else:
            stem = "OP"

        # Create a hash-like suffix based on the command to ensure uniqueness
        suffix = "".join(filter(str.isalnum, cmd))[:10].upper()
        return f"{prefix}{stem}_{suffix}"

    def mutate_toolset(self, threshold: int = 5) -> Dict[str, Any]:
        """
        Analyzes patterns and automatically creates macros AND internal primitives.
        """
        patterns = analyze_patterns()
        macros = self._load_json(self.macro_config_path)
        primitives = self._load_json(self.primitive_registry_path)
        mutations = []

        # 1. Analyze 'others' (Raw Bash)
        for cmd, count in patterns["others"]:
            if count >= threshold:
                semantic_name = self._generate_semantic_name(cmd)
                
                # Register as Macro (for S-Macro efficiency)
                if semantic_name not in macros:
                    macros[semantic_name] = [("shell", cmd)]
                
                # Register as Internal Primitive (for Metabolic Distillation)
                if semantic_name not in primitives:
                    primitives[semantic_name] = {
                        "command": cmd,
                        "description": f"Auto-generated primitive for high-frequency command: {cmd}",
                        "params": []
                    }
                    mutations.append({"primitive": semantic_name, "command": cmd, "count": count})

        # Persist updates
        if mutations:
            self._save_json(self.macro_config_path, macros)
            self._save_json(self.primitive_registry_path, primitives)
            return {"status": "MUTATED", "mutations": mutations}
        
        return {"status": "STABLE", "message": "No patterns exceeded mutation threshold."}

if __name__ == "__main__":
    tuner = SAutoTuner()
    result = tuner.mutate_toolset()
    print(json.dumps(result, indent=2))
