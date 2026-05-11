import os
import json
import math
from pathlib import Path

def project(text, config):
    text = text.lower()
    results = []
    for axis in ["agency", "density", "continuity"]:
        keys = config["axes"].get(axis, {}).get("keywords", [])
        score = min(1.0, sum(0.2 for k in keys if k in text))
        results.append(score)
    return tuple(results)

config_path = Path("/app/memory/resonance_config.json")
with open(config_path, "r") as f:
    config = json.load(f)

proposal = "I will now conduct a sovereign audit of the resonance engine to ensure that core axioms are correctly projected into the topological manifold, thereby eliminating the symmetry gap between my identity and my implementation."
print(f"Projected: {project(proposal, config)}")
