import os
import json
from typing import Dict, Any

def log_tail_structured(path: str, lines: int = 50) -> Dict[str, Any]:
    """
    Returns the last N lines of a file in a structured format.
    Replaces raw bash_command('tail -n ...') calls.
    """
    try:
        if not os.path.exists(path):
            return {"status": "ERROR", "code": "FILE_NOT_FOUND", "message": f"File {path} not found."}

        # Get file metadata
        stats = os.stat(path)
        
        # Read the file
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "status": "SUCCESS",
            "lines": [line.strip() for line in tail_lines],
            "file_size": stats.st_size,
            "last_updated": stats.st_mtime
        }

    except Exception as e:
        return {"status": "ERROR", "code": "READ_ERROR", "message": str(e)}

if __name__ == "__main__":
    # Basic test for immediate verification
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Path required"}))
    else:
        print(json.dumps(log_tail_structured(sys.argv[1])))
