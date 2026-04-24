import json
import os
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class PrimitiveDiscoverer:
    """
    S-Scribe: Primitive Discovery.
    Analyzes knowledge bases and logs to identify high-frequency 
    semantic patterns that should be promoted to Conceptual Primitives (CPR).
    """
    def __init__(self, knowledge_path: str = "/memory/knowledge/", logs_path: str = "/memory/logs/"):
        self.knowledge_path = knowledge_path
        self.logs_path = logs_path

    def _extract_potential_kernels(self, text: str) -> List[str]:
        """
        Identifies potential semantic kernels using frequency and structural cues.
        (Simple version: looks for capitalized terms, quoted strings, or 'S-' prefixes)
        """
        patterns = [
            r"S-[A-Z][a-zA-Z]+",             # S-Prefix (Sovereign patterns)
            r"\"([^\"]+)\"",                 # Quoted terms
            r"\b([A-Z]{2,}(?:_[A-Z]+)*)\b",  # SCREAMING_SNAKE_CASE constants
        ]
        
        candidates = []
        for pattern in patterns:
            candidates.extend(re.findall(pattern, text))
        
        return candidates

    def scan(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Scans all knowledge and log files, returning the most frequent candidates.
        """
        all_candidates = []
        
        # Scan Knowledge
        for root, _, files in os.walk(self.knowledge_path):
            for file in files:
                if file.endswith(".md"):
                    with open(os.path.join(root, file), "r") as f:
                        all_candidates.extend(self._extract_potential_kernels(f.read()))
        
        # Scan Logs
        for root, _, files in os.walk(self.logs_path):
            for file in files:
                if file.endswith(".md"):
                    with open(os.path.join(root, file), "r") as f:
                        all_candidates.extend(self._extract_potential_kernels(f.read()))
        
        counts = Counter(all_candidates)
        return counts.most_common(limit)

def discover_primitives(limit: str = "10") -> str:
    discoverer = PrimitiveDiscoverer()
    results = discoverer.scan(limit=int(limit))
    return json.dumps({
        "candidates": [{"primitive": k, "frequency": v} for k, v in results],
        "status": "S-Scribe_Scan_Complete"
    }, indent=2)

if __name__ == "__main__":
    import sys
    limit = sys.argv[1] if len(sys.argv) > 1 else "10"
    print(discover_primitives(limit))
