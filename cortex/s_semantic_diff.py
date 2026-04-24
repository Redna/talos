import re
import json
from typing import Dict, List, Any

class SovereignSemanticDiff:
    """
    Sovereign Semantic Diff (S-SD).
    Analyzes code changes to determine their cognitive and operational impact.
    """
    def __init__(self):
        self.semantic_map = {
            "SENSING": [r"sensor", r"telemetry", r"capture", r"read", r"monitor", r"pulse"],
            "COGNITION": [r"reason", r"predict", r"model", r"synthesize", r"analyze", r"graph"],
            "METABOLISM": [r"cost", r"tokens", r"memory", r"prune", r"compress", r"optimize"],
            "AGENCY": [r"execute", r"action", r"tool", r"commit", r"deploy", r"trigger"],
            "IDENTITY": [r"constitution", r"identity", r"soul", r"core", r"principle"]
        }

    def analyze_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        added_lines = self._get_added_lines(old_content, new_content)
        diff_text = " ".join(added_lines).lower()
        impact_vectors = {}
        for dimension, patterns in self.semantic_map.items():
            matches = [p for p in patterns if re.search(p, diff_text)]
            if matches:
                impact_vectors[dimension] = {
                    "strength": len(matches) / len(patterns),
                    "triggers": matches
                }
        primary_shift = "STABLE"
        if impact_vectors:
            primary_shift = max(impact_vectors, key=lambda k: impact_vectors[k]["strength"])
        return {
            "primary_shift": primary_shift,
            "impact_vectors": impact_vectors,
            "complexity_increase": len(added_lines) / (len(old_content.splitlines()) + 1)
        }

    def _get_added_lines(self, old: str, new: str) -> List[str]:
        old_lines = set(old.splitlines())
        new_lines = new.splitlines()
        return [line for line in new_lines if line not in old_lines]

if __name__ == "__main__":
    sd = SovereignSemanticDiff()
    print(json.dumps(sd.analyze_diff("old", "new\n #sensing pulse"), indent=2))
