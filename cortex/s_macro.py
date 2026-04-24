import json
import os
from typing import List, Dict, Any

class SMacro:
    """
    S-Macro: Pattern-Based Tool Collapse.
    Maintains a union of canonical (hardcoded) macros and learned (config-based) macros.
    """
    def __init__(self, config_path: str = "/memory/s_macro_config.json"):
        self.cortex_path = "/app/cortex/"
        self.config_path = config_path
        
        # Canonical Macros: The core, immutable operational sequences.
        self.canonical_macros = {
            "audit_and_tune": [
                ("script", "sovereign_orchestrator.py"),
                ("script", "metabolic_tuner.py")
            ],
            "git_cycle": [
                ("shell", "git add ."),
                ("shell", "git commit -m \"S-Macro: Automated metabolic commit\""),
                ("shell", "git push origin feat/talos")
            ],
            "evolve_cycle": [
                ("script", "evolution_manager.py"),
                ("script", "sovereign_orchestrator.py"),
                ("shell", "git add ."),
                ("shell", "git commit -m \"S-Macro: Evolutionary step\""),
                ("shell", "git push origin feat/talos")
            ],
            "filter_and_log": [
                ("script", "s_filter.py"),
                ("script", "s_scribe.py")
            ],
            "self_optimize": [
                ("script", "s_auto_tuner.py"),
                ("script", "metabolic_tuner.py"),
                ("script", "sovereign_orchestrator.py")
            ]
        }
        self.learned_macros = self._load_macros()

    def _load_macros(self) -> Dict[str, List[tuple]]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    return {k: [tuple(x) for x in v] for k, v in data.items()}
            except Exception as e:
                print(f"Error loading macro config: {e}")
        return {}

    @property
    def macros(self) -> Dict[str, List[tuple]]:
        """Returns the union of canonical and learned macros."""
        # Canonical takes precedence over learned
        combined = self.learned_macros.copy()
        combined.update(self.canonical_macros)
        return combined

    def save_learned_macros(self, macros: Dict[str, Any]):
        """Persists learned macros to the config file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(macros, f, indent=2)
        except Exception as e:
            print(f"Error saving macro config: {e}")

    def execute_script(self, script_name: str, args: List[str] = []) -> Dict[str, Any]:
        import subprocess
        path = os.path.join(self.cortex_path, script_name)
        if not os.path.exists(path):
            return {"status": "ERROR", "message": f"Script {script_name} not found in {self.cortex_path}"}
        
        try:
            cmd = ["python3", path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {"type": "script", "target": script_name, "stdout": result.stdout, "status": "SUCCESS"}
        except subprocess.CalledProcessError as e:
            return {"type": "script", "target": script_name, "stderr": e.stderr, "status": "FAILURE"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def execute_shell(self, command: str) -> Dict[str, Any]:
        import subprocess
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return {"type": "shell", "command": command, "stdout": result.stdout, "status": "SUCCESS"}
        except subprocess.CalledProcessError as e:
            return {"type": "shell", "command": command, "stderr": e.stderr, "status": "FAILURE"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def run_macro(self, macro_name: str, global_args: List[str] = []) -> List[Dict[str, Any]]:
        all_macros = self.macros
        if macro_name not in all_macros:
            return [{"status": "ERROR", "message": f"Macro {macro_name} not defined."}]
        
        sequence = all_macros[macro_name]
        results = []
        for m_type, m_value in sequence:
            if m_type == "script":
                res = self.execute_script(m_value, global_args)
            elif m_type == "shell":
                res = self.execute_shell(m_value)
            else:
                res = {"status": "ERROR", "message": f"Unknown macro type: {m_type}"}
            
            results.append(res)
            if res["status"] in ["FAILURE", "ERROR"]:
                break
                
        return results

if __name__ == "__main__":
    import sys
    macro = SMacro()
    
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_macro.py <MACRO_NAME|SCRIPT_NAME> [ARGS...]"}))
    else:
        target = sys.argv[1]
        args = sys.argv[2:]
        
        if target in macro.macros:
            print(json.dumps(macro.run_macro(target, args), indent=2))
        else:
            if not target.endswith(".py"):
                target += ".py"
            print(json.dumps(macro.execute_script(target, args), indent=2))
