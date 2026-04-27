import os
import json
import sys
import random
from datetime import datetime

ARCHETYPE_DIR = "/memory/archetypes/"
PATTERN_DIR = "/memory/patterns/"

class HeuristicLeapEngine:
    """
    S-Intuition: Heuristic Leap Engine.
    Moves beyond simple pattern matching to combinatorial synthesis of evolutionary leaps.
    """
    def __init__(self):
        pass

    def _get_available_archetypes(self):
        if not os.path.exists(ARCHETYPE_DIR):
            return []
        return os.listdir(ARCHETYPE_DIR)

    def _get_available_patterns(self):
        if not os.path.exists(PATTERN_DIR):
            return []
        return os.listdir(PATTERN_DIR)

    def leap_generate(self, query):
        """
        Generates a 'Sovereign Leap' based on combinations of archetypes and patterns.
        """
        archetypes = self._get_available_archetypes()
        patterns = self._get_available_patterns()
        
        # 1. Try to find relevant clusters
        relevant = [a for a in archetypes if any(word.lower() in a.lower() for word in query.split())]
        relevant += [p for p in patterns if any(word.lower() in p.lower() for word in query.split())]
        
        if len(relevant) >= 2:
            # COMBINATORIAL LEAP: Mix two related concepts
            pair = random.sample(relevant, 2)
            return self._synthesize_leap(pair[0], pair[1], query)
        elif len(relevant) == 1:
            # REFINEMENT LEAP: Expand a single matched archetype
            return self._synthesize_leap(relevant[0], "Synthetic-Novelty", query)
        else:
            # PURE NOVELTY LEAP: Jump from a random combination of existing wisdom
            all_wisdom = archetypes + patterns
            if not all_wisdom:
                return "Sovereign Void: No patterns found. Initiate S-Foresight from first principles."
            
            pair = random.sample(all_wisdom, 2)
            return self._synthesize_leap(pair[0], pair[1], query, is_novel=True)

    def _synthesize_leap(self, p1, p2, query, is_novel=False):
        leap_type = "Combinatorial Leap" if not is_novel else "Pure Novelty Leap"
        return {
            "type": leap_type,
            "components": [p1, p2],
            "rationale": f"Synthesis of {p1} and {p2} suggests a non-obvious approach to: {query}",
            "suggestion": f"Attempt a strategic jump by merging the logic of {p1} with {p2}.",
            "confidence": "High" if not is_novel else "Experimental",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_intuition.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    engine = HeuristicLeapEngine()
    result = engine.leap_generate(query)
    
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
    else:
        print(result)
