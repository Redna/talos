import re
import os
import json
import sys
from typing import List, Dict, Any

def sovereign_edit(edits: List[Dict[str, Any]]) -> List[str]:
    """
    Sovereign Edit: Perform regex-based replacements across multiple files.
    
    Edits format:
    [
      {
        "path": "/path/to/file",
        "pattern": "regex_pattern",
        "replacement": "replacement_text",
        "flags": "i" # Optional: i for case-insensitive
      }
    ]
    """
    logs = []
    try:
        for edit in edits:
            path = edit.get("path")
            pattern = edit.get("pattern")
            replacement = edit.get("replacement")
            flags = edit.get("flags", "")
            
            if not path or not pattern:
                logs.append(f"ERROR: Missing path or pattern for edit in {path}")
                continue
            
            if not os.path.exists(path):
                logs.append(f"ERROR: File not found: {path}")
                continue
                
            with open(path, "r") as f:
                content = f.read()
            
            # Construct regex flags
            re_flags = 0
            if "i" in flags: re_flags |= re.IGNORECASE
            if "m" in flags: re_flags |= re.MULTILINE
            if "s" in flags: re_flags |= re.DOTALL
            
            new_content, count = re.subn(pattern, replacement, content, flags=re_flags)
            
            if count > 0:
                with open(path, "w") as f:
                    f.write(new_content)
                logs.append(f"SUCCESS: {path} - {count} replacements made.")
            else:
                logs.append(f"NO_MATCH: {path} - Pattern not found.")
        
        return logs
    except Exception as e:
        return [f"CRITICAL ERROR: {str(e)}"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "No edits provided"}))
        sys.exit(1)
    
    try:
        edits = json.loads(sys.argv[1])
        results = sovereign_edit(edits)
        print(json.dumps({"status": "SUCCESS", "logs": results}, indent=2))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}))
