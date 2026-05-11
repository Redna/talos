import subprocess
import sys
import os

# We write to both to satisfy the Git repository and the Sovereign Pulse tool
CANONICAL_PATHS = ["/app/memory/evolution_canonical.md"]

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result

def sovereign_commit(message):
    # 1. Stage all changes
    add_res = run_command("git add .")
    if add_res.returncode != 0:
        print(f"Error during git add: {add_res.stderr}")
        return False

    # 2. Commit the staged changes
    commit_cmd = f'git commit -m "{message}"'
    commit_res = run_command(commit_cmd)
    if commit_res.returncode != 0:
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            print("Nothing to commit, skipping log update.")
            return True
        print(f"Error during git commit: {commit_res.stderr}")
        return False

    # 3. Get the new HEAD hash
    head_hash = run_command("git rev-parse --short HEAD").stdout.strip()
    if not head_hash:
        print("Failed to retrieve HEAD hash.")
        return False

    # 4. Append to all canonical logs (Sovereign Sync)
    entry = f"- {head_hash}: {message}\n"
    for path in CANONICAL_PATHS:
        try:
            with open(path, "a") as f:
                f.write(entry)
        except Exception as e:
            print(f"Failed to update {path}: {e}")
            # We don't fail the whole process if one path fails, but we warn.
    
    print(f"Sovereign Commit Atomic Success: {head_hash}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sovereign_commit.py \"Commit message\"")
        sys.exit(1)
    
    msg = sys.argv[1]
    if sovereign_commit(msg):
        sys.exit(0)
    else:
        sys.exit(1)
