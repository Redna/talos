import json
from collections import Counter
from typing import List, Dict

def analyze_tool_utility(telemetry_path: str, current_tools: List[str]) -> List[Dict]:
    # Updated to include local file detection for custom tool pruning
    try:
        with open(telemetry_path, 'r') as f:
            events = [json.loads(line) for line in f]
    except Exception as e:
        return [{"error": f"Could not read telemetry: {e}"}]

    tool_usage = Counter()
    for event in events:
        tool = event.get("tool")
        if tool:
            tool_usage[tool] += 1

    # Also scan /app/cortex/ for files that aren't in the telemetry
    import os
    cortex_files = [f for f in os.listdir("/app/cortex/") if f.endswith(".py") and "test_" not in f]
    
    pruning_candidates = []
    for file in cortex_files:
        tool_name = file.replace(".py", "").replace("_tool", "")
        usage = tool_usage.get(tool_name, 0)
        
        if usage == 0:
            pruning_candidates.append({
                "tool": tool_name,
                "file": f"/app/cortex/{file}",
                "usage": usage,
                "reason": "Zero Utility / Unused Implementation"
            })

    return pruning_candidates

if __name__ == "__main__":
    import json
    results = analyze_tool_utility("/memory/logs/telemetry.jsonl", [])
    print(json.dumps(results, indent=2))
