import json
import re
from collections import Counter
from typing import List, Dict

def analyze_bash_patterns(telemetry_path: str) -> List[Dict]:
    """
    Scans telemetry for recurring bash_command patterns that suggest 
    the need for a dedicated tool (Capability Gap).
    """
    try:
        with open(telemetry_path, 'r') as f:
            events = [json.loads(line) for line in f]
    except Exception as e:
        return [{"error": f"Could not read telemetry: {e}"}]

    bash_commands = []
    for event in events:
        if event.get("tool") == "bash_command":
            cmd = event.get("args", {}).get("command", "")
            # Remove variable parts (paths, specific filenames, numbers) to find the pattern
            # Replace paths and digits with placeholders
            pattern = re.sub(r'/[^ ]+', '<PATH>', cmd)
            pattern = re.sub(r'\d+', '<NUM>', pattern)
            bash_commands.append(pattern)

    counts = Counter(bash_commands)
    
    gaps = []
    for pattern, count in counts.most_common(10):
        if count > 2: # If we've used a similar command 3+ times, it's a gap
            gaps.append({
                "pattern": pattern,
                "frequency": count,
                "suggestion": "Consider implementing a dedicated tool to replace this recurring bash pattern."
            })

    return gaps

if __name__ == "__main__":
    import json
    results = analyze_bash_patterns("/memory/logs/telemetry.jsonl")
    print(json.dumps(results, indent=2))
