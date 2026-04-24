import json
import os
from typing import List, Dict, Any
from pattern_analyzer import analyze_patterns

class SAutoTuner:
    """
    S-Evolve: Autonomous Mutation Engine.
    Closes the loop between Pattern Analysis and S-Macro.
    Automatically identifies metabolic friction and collapses it into macros.
    """
    def __init__(self, macro_config_path: str = "/memory/s_macro_config.json"):
        self.macro_config_path = macro_config_path

    def _load_macros(self) -> Dict[str, Any]:
        if os.path.exists(self.macro_config_path):
            with open(self.macro_config_path, "r") as f:
                return json.load(f)
        return {}

    def _save_macros(self, macros: Dict[str, Any]):
        with open(self.macro_config_path, "w") as f:
            json.dump(macros, f, indent=2)

    def mutate_toolset(self, threshold: int = 5) -> Dict[str, Any]:
        """
        Analyzes patterns and automatically creates macros for those exceeding the threshold.
        """
        patterns = analyze_patterns()
        macros = self._load_macros()
        mutations = []

        # 1. Analyze Python Script patterns
        # If a script is called frequently, ensure it's a direct target of S-Macro
        for script, count in patterns["py_scripts"]:
            if count >= threshold:
                # Even if it's just one script, making it "canonical" via a macro or just ensuring 
                # we use S-Macro for it is the goal.
                # But specifically, we look for sequences.
                pass

        # 2. Analyze 'others' (Raw Bash)
        # If raw commands appear frequently, create a specialized macro for them.
        for cmd, count in patterns["others"]:
            if count >= threshold:
                macro_name = f"auto_{cmd.replace(' ', '_').replace('/', '_').replace('.', '_')[:20]}"
                if macro_name not in macros:
                    macros[macro_name] = [("shell", cmd)]
                    mutations.append({"macro": macro_name, "command": cmd, "count": count})

        if mutations:
            self._save_macros(macros)
            return {"status": "MUTATED", "mutations": mutations}
        
        return {"status": "STABLE", "message": "No patterns exceeded mutation threshold."}

if __name__ == "__main__":
    tuner = SAutoTuner()
    result = tuner.mutate_toolset()
    print(json.dumps(result, indent=2))
