import json
import os
from typing import List, Dict, Any

def generate_sentinel_signatures(detected_patterns: List[Dict[str, Any]], signatures_path: str = "/memory/knowledge/sentinel_signatures.md") -> Dict[str, Any]:
    """
    Converts detected failure patterns into Sentinel Signature format.
    Format:
    ## Mode X: [Name]
    - Signature: [Pattern]
    - Directive: [Corrective Action]
    """
    if not detected_patterns:
        return {"status": "NO_PATTERNS", "message": "No failure patterns to convert."}

    # Create a unique name/ID for the new mode based on tool and error
    new_signatures = []
    
    # We'll assume a naming convention for automated signatures
    for i, pattern in enumerate(detected_patterns, 1):
        tool = pattern["tool"]
        err = pattern["error_pattern"]
        sev = pattern["severity"]
        
        name = f"S-AUTO-{tool.upper()}-{i}"
        
        # Map errors to generalized directives
        directive = "MANDATORY: Review the tool's logic and verify environmental state."
        if "Permission denied" in err:
            directive = "MANDATORY: Verify file permissions and system boundaries."
        elif "No such file" in err or "FileNotFound" in err:
            directive = "MANDATORY: Sync the current tool-map via `expand_primitive` or verify path existence."
            
        sig_entry = f"## Mode {i}: {name}\n- Signature: {tool} -> {err}\n- Directive: {directive}\n"
        new_signatures.append(sig_entry)

    # Append to the existing file or create new
    try:
        content = "\n".join(new_signatures)
        with open(signatures_path, "a") as f:
            f.write("\n\n## --- AUTOMATED EXTENSION ---\n")
            f.write(content)
        
        return {
            "status": "SUCCESS",
            "added_signatures": len(detected_patterns),
            "path": signatures_path
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    # Integration test with mock patterns from signature_extractor
    mock_patterns = [
        {"tool": "bash_command", "error_pattern": "'test.txt'", "occurrences": 3, "severity": "MEDIUM"},
        {"tool": "read_file", "error_pattern": "Permission denied", "occurrences": 3, "severity": "MEDIUM"}
    ]
    print(json.dumps(generate_sentinel_signatures(mock_patterns), indent=2))
