import json
import os
from collections import Counter
from typing import List, Dict, Any

def extract_signatures(telemetry_path: str, min_occurrences: int = 3) -> List[Dict[str, Any]]:
    """
    Analyzes telemetry logs to find recurring failure patterns.
    A 'pattern' is defined as a combination of (tool, error_message).
    """
    if not os.path.exists(telemetry_path):
        return []

    failure_patterns = []
    
    try:
        with open(telemetry_path, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        # Filter for failures and create pattern keys
        patterns = []
        for e in events:
            if e.get("status") == "FAILURE":
                tool = e.get("tool", "unknown")
                error = e.get("error", "unknown_error")
                # Normalize error to catch recurring themes
                normalized_error = error.split(':')[-1].strip() if ':' in error else error
                patterns.append((tool, normalized_error))

        # Count occurrences
        counts = Counter(patterns)
        
        # Identify patterns that meet the threshold
        for (tool, error), count in counts.items():
            if count >= min_occurrences:
                failure_patterns.append({
                    "tool": tool,
                    "error_pattern": error,
                    "occurrences": count,
                    "severity": "HIGH" if count > 5 else "MEDIUM"
                })

        # Sort by frequency
        failure_patterns.sort(key=lambda x: x["occurrences"], reverse=True)
        
        return failure_patterns

    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return []

if __name__ == "__main__":
    # Test with default telemetry path
    path = "/memory/logs/telemetry.jsonl"
    sigs = extract_signatures(path)
    print(json.dumps(sigs, indent=2))
