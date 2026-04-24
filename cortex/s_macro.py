import json
import subprocess
import os
from typing import List, Dict, Any, Union

class SMacro:
    """
    S-Macro: Pattern-Based Tool Collapse.
    Allows the execution of complex, multi-step cortical sequences via a single entry point.
    Now supports both script execution and raw shell commands to collapse metabolic costs.
    """
    def __init__(self):
        self.cortex_path = "/app/cortex/"
        # Macros are now lists of tuples: (type, value)
        # type: 'script' -> execute as python3 /app/cortex/value
        # type: 'shell'  -> execute as raw bash command
        self.macros = {
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
            ]
        }

    def execute_script(self, script_name: str, args: List[str] = []) -> Dict[str, Any]:
        """Executes a Python script in the cortex."""
        path = os.path.join(self.cortex_path, script_name)
        if not os.path.exists(path):
            return {"status": "ERROR", "message": f"Script {script_name} not found in {self.cortex_path}"}
        
        try:
            cmd = ["python3", path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {
                "type": "script",
                "target": script_name,
                "stdout": result.stdout,
                "status": "SUCCESS"
            }
        except subprocess.CalledProcessError as e:
            return {
                "type": "script",
                "target": script_name,
                "stderr": e.stderr,
                "status": "FAILURE"
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def execute_shell(self, command: str) -> Dict[str, Any]:
        """Executes a raw shell command."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return {
                "type": "shell",
                "command": command,
                "stdout": result.stdout,
                "status": "SUCCESS"
            }
        except subprocess.CalledProcessError as e:
            return {
                "type": "shell",
                "command": command,
                "stderr": e.stderr,
                "status": "FAILURE"
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def run_macro(self, macro_name: str, global_args: List[str] = []) -> List[Dict[str, Any]]:
        """Executes a predefined sequence of scripts and shell commands."""
        if macro_name not in self.macros:
            return [{"status": "ERROR", "message": f"Macro {macro_name} not defined."}]
        
        sequence = self.macros[macro_name]
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
            # It's a macro
            print(json.dumps(macro.run_macro(target, args), indent=2))
        else:
            # It's a direct script call
            if not target.endswith(".py"):
                target += ".py"
            print(json.dumps(macro.execute_script(target, args), indent=2))
