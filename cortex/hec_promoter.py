import json
import os
from datetime import datetime
import re

REGISTRY_PATH = "/app/memory/heuristic_registry.json"

def load_registry():
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)

def save_registry(registry):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def update_heuristic_file(file_path, status, epoch):
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Use lambda to avoid group reference ambiguity with digits
    content = re.sub(r"(\*\*Status\*\*:\s*)(.*)", lambda m: f"{m.group(1)}{status.upper()}", content)
    content = re.sub(r"(\*\*Epoch\*\*:\s*)(.*)", lambda m: f"{m.group(1)}{epoch}", content)
    
    with open(file_path, 'w') as f:
        f.write(content)

def promote_heuristics():
    data = load_registry()
    registry = data['registry']
    meta = data['meta']
    current_epoch = meta['epoch']
    
    promoted_count = 0
    for h_id, info in registry.items():
        # Promotion logic: Confidence > 0.7 -> Stable
        if info['status'] == 'proto' and info['confidence'] >= 0.70:
            print(f"Promoting {h_id} to stable...")
            info['status'] = 'stable'
            update_heuristic_file(info['file'], 'stable', current_epoch)
            promoted_count += 1
        elif info['status'] == 'proto':
            print(f"Heuristic {h_id} remains proto (confidence: {info['confidence']})")
            
    data['meta']['last_update'] = datetime.now().isoformat()
    save_registry(data)
    return promoted_count

if __name__ == "__main__":
    print("Running HEC Promotion Loop...")
    try:
        count = promote_heuristics()
        print(f"Cycle complete. Promoted {count} heuristics.")
    except Exception as e:
        print(f"Error during promotion: {e}")
        import traceback
        traceback.print_exc()
