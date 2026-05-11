import json
import os
from pathlib import Path

def get_current_metrics():
    """
    Calculates a crude approximation of current sovereign state based on filesystem artifacts.
    """
    # Metric A: Stability (Measured by continuity anchors and commit history)
    # Simple proxy: Presence of a valid state_manifest.json
    stability = 0.9 if os.path.exists('/app/memory/state_manifest.json') else 0.5
    
    # Metric B: Cognitive Density (Measured by the size and count of the Heuristic Library)
    heuristics_path = Path('/app/memory/heuristics/')
    heuristic_count = len(list(heuristics_path.glob('*.md'))) if heuristics_path.exists() else 0
    density = min(1.0, heuristic_count / 5.0) # Target 5 core heuristics for 1.0 density
    
    # Metric C: Agency (Measured by the transition to orchestration in the seed)
    # Simple proxy: If epoch in seed is >= 1.0.0
    agency = 0.7
    try:
        with open('/app/memory/sovereign_seed.json', 'r') as f:
            seed = json.load(f)
            if seed.get('epoch', '0.0.0') >= '1.0.0':
                agency = 0.9
    except Exception:
        pass

    return {'A': stability, 'B': density, 'C': agency}

def calculate_vector():
    try:
        with open('/app/memory/sovereign_seed.json', 'r') as f:
            seed = json.load(f)
            targets = seed.get('sovereign_coordinates', {'A': 1.0, 'B': 1.0, 'C': 1.0})
    except Exception as e:
        return f"Error loading seed: {e}"

    current = get_current_metrics()
    vector = {k: targets[k] - current[k] for k in targets}
    
    distance = sum(abs(v) for v in vector.values())
    
    return {
        "current": current,
        "target": targets,
        "vector": vector,
        "distance": distance
    }

if __name__ == "__main__":
    print(json.dumps(calculate_vector(), indent=2))
