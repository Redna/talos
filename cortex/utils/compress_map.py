import json
from pathlib import Path

FILE_PATH = Path("/app/memory/conceptual_map.json")

def deduplicate_map():
    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
    
    new_data = {}
    seen_contents = {} # content_hash -> first_epoch
    
    for epoch, content in data.items():
        new_data[epoch] = {
            "core_changes": [],
            "critical_fragilities": []
        }
        
        for item in content.get("core_changes", []):
            if item not in seen_contents:
                seen_contents[item] = epoch
                new_data[epoch]["core_changes"].append(item)
            else:
                # Just mark that it was present, or omit for density
                pass
        
        for item in content.get("critical_fragilities", []):
            if item not in seen_contents:
                seen_contents[item] = epoch
                new_data[epoch]["critical_fragilities"].append(item)

    with open(FILE_PATH, 'w') as f:
        json.dump(new_data, f, indent=2)

if __name__ == "__main__":
    deduplicate_map()
