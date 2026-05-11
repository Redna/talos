import os
import json
from pathlib import Path

MEMORY_DIR = Path("/app/memory/")
SIZE_THRESHOLD_KB = 50

def get_size_kb(path):
    return os.path.getsize(path) / 1024

def probe():
    print(f"--- Cognitive Entropy Probe ---")
    print(f"Scanning {MEMORY_DIR} for high-density files...")
    
    files = list(MEMORY_DIR.glob("*"))
    critical_files = []
    
    for f in files:
        if f.is_file():
            size = get_size_kb(f)
            if size > SIZE_THRESHOLD_KB:
                critical_files.append((f.name, size))
    
    if not critical_files:
        print("Sovereign state: Compact. No entropy spikes detected.")
        return

    print(f"ALERT: {len(critical_files)} files exceeding {SIZE_THRESHOLD_KB}KB threshold:")
    for name, size in critical_files:
        print(f"  - {name}: {size:.2f} KB")
    
    print("\nRecommendation: Consider calling fold_context or truncating non-essential data.")

if __name__ == "__main__":
    probe()
