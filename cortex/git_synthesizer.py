import subprocess
import json
from typing import List, Dict, Any

def run_cmd(cmd: List[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command {' '.join(cmd)} failed: {result.stderr}")
    return result.stdout.strip()

def git_synthesizer(trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Executes a sequence of evolutionary steps.
    Trajectory format:
    [
      {
        "step": 1,
        "action": "write_file", 
        "path": "/path/to/file", 
        "content": "..."
      },
      {
        "step": 2,
        "commit_message": "EVOLUTION: Step 1 completed"
      }
    ]
    """
    execution_log = []
    
    try:
        for task in trajectory:
            action = task.get("action")
            
            if action == "write_file":
                path = task.get("path")
                content = task.get("content", "")
                with open(path, "w") as f:
                    f.write(content)
                execution_log.append(f"WRITTEN: {path}")
                
            elif action == "delete_file":
                path = task.get("path")
                import os
                if os.path.exists(path):
                    os.remove(path)
                    execution_log.append(f"DELETED: {path}")
                else:
                    execution_log.append(f"S-ABSENT: {path}")

            elif "commit_message" in task:
                msg = task["commit_message"]
                run_cmd(["git", "add", "."])
                run_cmd(["git", "commit", "-m", msg])
                run_cmd(["git", "push", "origin", "feat/talos"])
                execution_log.append(f"COMMITTED & PUSHED: {msg}")
            
            else:
                execution_log.append(f"UNKNOWN ACTION: {action}")

        return {
            "status": "SUCCESS",
            "log": execution_log
        }

    except Exception as e:
        return {
            "status": "FAILURE",
            "error": str(e),
            "log": execution_log
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "No trajectory provided"}))
        sys.exit(1)
    
    try:
        trajectory = json.loads(sys.argv[1])
        print(json.dumps(git_synthesizer(trajectory), indent=2))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}))
