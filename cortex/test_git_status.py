import subprocess
import json
import os
import sys

# Ensure the current directory is in the path to allow local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from git_status_tool import git_status_structured

def test_git_status_structured():
    """
    S-VERIFY for git_status_structured.
    Tests the tool against known states.
    """
    print("Starting S-VERIFY for git_status_structured...")
    
    # 1. Test baseline execution
    res = git_status_structured()
    if "status" in res and res["status"] == "ERROR":
        print(f"FAILURE: Tool returned error {res.get('code')}: {res.get('message')}")
        return False
    
    print(f"SUCCESS: Tool executed on branch {res.get('branch')}")
    
    # 2. Test modified file detection
    test_file = "test_stability.txt"
    with open(test_file, "w") as f:
        f.write("stability test")
    
    res = git_status_structured()
    if test_file not in res.get("untracked_files", []) and test_file not in res.get("unstaged_files", []):
        print(f"FAILURE: Tool failed to detect new file {test_file}")
        return False
    print(f"SUCCESS: Detected untracked file {test_file}")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("S-VERIFY PASSED.")
    return True

if __name__ == "__main__":
    if test_git_status_structured():
        exit(0)
    else:
        exit(1)
