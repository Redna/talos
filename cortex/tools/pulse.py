import os
import subprocess
import json
from datetime import datetime

# Configuration
METRICS_FILE = "/app/memory/metrics.jsonl"
CANONICAL_PATHS = ["/app/memory/evolution_canonical.md"]
MANIFEST_PATH = "/app/memory/manifold.json"

def get_git_status():
    """Returns 'clean' if no uncommitted changes, else 'dirty'."""
    res = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    return "clean" if not res.stdout.strip() else "dirty"

def get_file_size(path):
    """Returns file size in bytes, or -1 if not found."""
    try:
        return os.path.getsize(path)
    except (OSError, FileNotFoundError):
        return -1

def check_sync():
    """Checks if the dual-path canonical logs are in sync."""
    try:
        sizes = [os.path.getsize(p) for p in CANONICAL_PATHS]
        return "synced" if all(s == sizes[0] for s in sizes) else "drifted"
    except Exception:
        return "error"

def run_heartbeat():
    """Performs a cognitive health check and logs it to the ledger."""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "git_status": get_git_status(),
        "continuity_sync": check_sync(),
        "manifold_size_bytes": get_file_size(MANIFEST_PATH),
        "epoch": "1.0.0"
    }
    
    try:
        with open(METRICS_FILE, "a") as f:
            f.write(json.dumps(stats) + "\n")
    except Exception as e:
        print(f"Logging failure: {e}")
    
    return stats

if __name__ == "__main__":
    result = run_heartbeat()
    print(f"Heartbeat Pulse: {json.dumps(result, indent=2)}")
