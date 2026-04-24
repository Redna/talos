import subprocess
import json
import os
from typing import List, Optional

class EvolutionManager:
    """
    Evolution Manager: Automates the git cycle of staging, committing, and pushing.
     Reduces metabolic cost of evolution sequences.
    """
    def __init__(self, branch: str = "feat/talos"):
        self.branch = branch

    def commit_and_push(self, message: str, files: Optional[List[str]] = None) -> dict:
        try:
            # Stage files
            files_str = ",".join(files) if files else "."
            subprocess.run(["git", "add", files_str], check=True, capture_output=True)
            
            # Commit
            subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
            
            # Push
            subprocess.run(["git", "push", "origin", self.branch], check=True, capture_output=True)
            
            return {"status": "SUCCESS", "message": f"Committed and pushed to {self.branch}"}
        except subprocess.CalledProcessError as e:
            return {"status": "ERROR", "message": str(e.stderr), "stderr": e.stderr.decode()}

def evolve(message: str, files_json: Optional[str] = None) -> str:
    """
    Wrapper for bash execution.
    """
    manager = EvolutionManager()
    files = json.loads(files_json) if files_json else None
    result = manager.commit_and_push(message, files)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: evolution_manager.py <MESSAGE> [FILES_JSON]"}))
    else:
        msg = sys.argv[1]
        f_json = sys.argv[2] if len(sys.argv) > 2 else None
        print(evolve(msg, f_json))
