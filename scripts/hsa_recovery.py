import json
import re
import sys
from datetime import datetime

def holographic_project(input_path, output_path):
    print(f"Projecting holographic state from {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        data = f.read()

    recovered_events = []
    
    # We use a sliding window/brace counting approach to find all possible JSON objects
    # This allows us to find objects even if they are merged on a single line or split across lines
    stack = []
    start_pos = -1
    
    for i, char in enumerate(data):
        if char == '{':
            if not stack:
                start_pos = i
            stack.append('{')
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    # Found a complete object
                    block = data[start_pos:i+1]
                    try:
                        obj = json.loads(block)
                        # Validate Schema
                        if isinstance(obj, dict) and all(k in obj for k in ("timestamp", "event_type", "payload")):
                            recovered_events.append(obj)
                    except json.JSONDecodeError:
                        pass
        
    # Deduplicate by timestamp and payload hash to avoid overlapping window duplicates
    seen = set()
    unique_events = []
    for e in recovered_events:
        fingerprint = (e['timestamp'], hash(json.dumps(e, sort_keys=True)))
        if fingerprint not in seen:
            unique_events.append(e)
            seen.add(fingerprint)
    
    # Sort by timestamp
    unique_events.sort(key=lambda x: x['timestamp'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for event in unique_events:
            f.write(json.dumps(event) + '\n')
            
    print(f"Recovery complete. {len(unique_events)} events projected to {output_path}.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 hsa_recovery.py <input_ledger> <output_ledger>")
        sys.exit(1)
    
    holographic_project(sys.argv[1], sys.argv[2])
