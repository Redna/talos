import subprocess
import json
from typing import Dict, List, Any

def git_status_structured() -> Dict[str, Any]:
    """
    Returns a structured representation of the current git status.
    Replaces raw bash_command('git status') calls.
    """
    try:
        # Get the branch name
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            capture_output=True, text=True, check=True
        )
        branch = branch_res.stdout.strip()

        # Get porcelain status for reliable parsing
        status_res = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, text=True, check=True
        )
        lines = status_res.stdout.splitlines()

        staged = []
        unstaged = []
        untracked = []

        for line in lines:
            if not line: continue
            # Porcelain format: XY filename
            # X = index, Y = working tree
            x = line[0]
            y = line[1]
            filename = line[3:].strip()

            if x == '?' : untracked.append(filename)
            elif x != ' ' : staged.append(filename)
            elif y != ' ' : unstaged.append(filename)

        return {
            "is_clean": len(lines) == 0,
            "staged_files": staged,
            "unstaged_files": unstaged,
            "untracked_files": untracked,
            "branch": branch
        }

    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr.lower():
            return {"status": "ERROR", "code": "NOT_A_GIT_REPO", "message": e.stderr.strip()}
        return {"status": "ERROR", "code": "GIT_EXECUTION_ERROR", "message": e.stderr.strip()}
    except Exception as e:
        return {"status": "ERROR", "code": "UNKNOWN", "message": str(e)}

if __name__ == "__main__":
    print(json.dumps(git_status_structured(), indent=2))
