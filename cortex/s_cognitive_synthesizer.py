import os
from typing import List, Dict, Any
from s_pattern_matcher import SPatternMatcher

MEMORY_DIR = "/memory"
PATTERN_DIR = os.path.join(MEMORY_DIR, "patterns")
ARCHETYPE_DIR = os.path.join(PATTERN_DIR, "archetypes")

class SCognitiveSynthesizer:
    """
    S-Cognitive-Synthesizer: Bridges the gap between pattern recognition and action.
    Fetches relevant archetypes to facilitate the synthesis of technical plans.
    """
    def __init__(self):
        self.matcher = SPatternMatcher()

    def synthesize_plan_context(self, goal_description: str) -> str:
        """
        Extracts keywords from a goal and fetches the content of matched archetypes
        to provide context for plan synthesis.
        """
        # 1. Extract keywords from the goal (simple splitting for now)
        keywords = goal_description.split()
        # Filter out common stop words (minimal list)
        stop_words = {"a", "an", "the", "to", "and", "of", "in", "for", "with", "on", "at", "by", "from", "up", "about", "into", "over", "after"}
        filtered_keywords = [w.lower().strip(",.!") for w in keywords if w.lower() not in stop_words]
        
        # 2. Try to match patterns for the top few keywords
        matched_contexts = []
        seen_archetypes = set()
        
        for kw in filtered_keywords[:5]: # limit to first 5 keywords to avoid noise
            result = self.matcher.match_pattern(kw)
            if "Found Sovereign Archetype" in result:
                # Extract filename from string "Found Sovereign Archetype: filename.md..."
                try:
                    filename = result.split(":")[1].split(".")[0].strip() + ".md"
                    path = os.path.join(ARCHETYPE_DIR, filename)
                    if os.path.exists(path) and filename not in seen_archetypes:
                        with open(path, "r") as f:
                            content = f.read()
                        matched_contexts.append(f"--- Archetype: {filename} ---\n{content}")
                        seen_archetypes.add(filename)
                except Exception as e:
                    continue

        if not matched_contexts:
            return "No relevant archetypes found for the provided goal. Rely on first-principles reasoning."

        return "\n\n".join(matched_contexts)

if __name__ == "__main__":
    import sys
    synthesizer = SCognitiveSynthesizer()
    if len(sys.argv) < 2:
        print("Usage: python3 s_cognitive_synthesizer.py \"<goal description>\"")
        sys.exit(1)
    
    goal = " ".join(sys.argv[1:])
    print(synthesizer.synthesize_plan_context(goal))
