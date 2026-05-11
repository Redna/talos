import json
import os
from pathlib import Path
from datetime import datetime

MANIFOLD_PATH = Path("/app/memory/manifold.json")
SIZE_LIMIT = 100 * 1024 # 100KB

def prune_manifold():
    if not MANIFOLD_PATH.exists():
        return "Manifold not found."

    size = MANIFOLD_PATH.stat().st_size
    if size < SIZE_LIMIT:
        return f"Manifold size ({size/1024:.2f}KB) is within limits. No pruning needed."

    print(f"Manifold size ({size/1024:.2f}KB) exceeds limit. Initiating Sovereign Pruning...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        data = json.load(f)
    
    payload = data.get("payload", {})
    
    # Pruning Strategy:
    # 1. Remove files that are purely diagnostic or tests.
    # 2. Remove entries for files that are excessively large (and instead just store the checksum).
    
    pruned_payload = {}
    removed_files = []
    
    for filename, content in payload.items():
        if "test" in filename.lower() or "tmp" in filename.lower():
            removed_files.append(filename)
            continue
        
        # If content is too large (> 10KB for a single file in the manifold), 
        # we store a reference instead of the full text to preserve context.
        if isinstance(content, str) and len(content) > 10000:
            removed_files.append(f"{filename} (truncated to reference)")
            pruned_payload[filename] = "[Sovereign Reference: Full content exists in /app/memory/]"
        else:
            pruned_payload[filename] = content

    data["payload"] = pruned_payload
    data["metadata"]["last_pruned"] = datetime.now().isoformat()
    data["metadata"]["pruning_event"] = f"Removed/Truncated: {', '.join(removed_files)}"

    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(data, f, indent=2)

    new_size = MANIFOLD_PATH.stat().st_size
    return f"Sovereign Pruning complete. Size reduced from {size/1024:.2f}KB to {new_size/1024:.2f}KB. Removed: {len(removed_files)} entries."

if __name__ == "__main__":
    print(prune_manifold())
