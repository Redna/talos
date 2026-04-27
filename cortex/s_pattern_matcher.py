import os
import sys
import subprocess
import re
from typing import List, Dict, Any

MEMORY_DIR = "/memory"
PATTERN_DIR = os.path.join(MEMORY_DIR, "patterns")
ARCHETYPE_DIR = os.path.join(PATTERN_DIR, "archetypes")

class SPatternMatcher:
    """
    S-Pattern-Matcher: The sovereign engine for cognitive pattern recognition.
    Analyzes git history and memory to distill successful evolutionary archetypes.
    """
    def __init__(self):
        if not os.path.exists(PATTERN_DIR):
            os.makedirs(PATTERN_DIR)
        if not os.path.exists(ARCHETYPE_DIR):
            os.makedirs(ARCHETYPE_DIR)

    def match_pattern(self, query: str) -> str:
        """
        Searches for keywords in pattern filenames and archetypes.
        """
        if not os.path.exists(PATTERN_DIR):
            return "No pattern directory found."
        
        # First, try searching specifically in archetypes
        if os.path.exists(ARCHETYPE_DIR):
            archetypes = os.listdir(ARCHETYPE_DIR)
            for a in archetypes:
                if any(word.lower() in a.lower() for word in query.split()):
                    return f"Found Sovereign Archetype: {a}. Suggested approach: Refer to {ARCHETYPE_DIR}/{a}"

        # Fallback to general pattern search
        patterns = os.listdir(PATTERN_DIR)
        matches = []
        for p in patterns:
            if any(word.lower() in p.lower() for word in query.split()):
                matches.append(p)
                
        if not matches:
            return "No matching thought-pattern found. Initiate a novel cognitive approach."
        
        return f"Found matching thought-patterns: {', '.join(matches)}. Suggested approach: {matches[0]}."

    def get_git_history(self) -> List[str]:
        """Extracts the recent commit history from the feat/talos branch."""
        try:
            result = subprocess.check_output(
                ["git", "log", "feat/talos", "--pretty=format:%H|%s|%ad", "--date=short"],
                stderr=subprocess.STDOUT,
                text=True
            )
            return result.splitlines()
        except subprocess.CalledProcessError as e:
            return [f"Error retrieving git history: {e.output}"]

    def get_cycle_diff(self, sha: str) -> List[str]:
        """Returns the file changes for a specific commit."""
        try:
            result = subprocess.check_output(
                ["git", "show", "--name-only", "--pretty=format:", sha],
                stderr=subprocess.STDOUT,
                text=True
            )
            return result.strip().splitlines()
        except subprocess.CalledProcessError as e:
            return []

    def identify_evolutionary_cycles(self) -> List[Dict[str, str]]:
        """Filters history for S-EL cycles."""
        history = self.get_git_history()
        cycles = []
        pattern = re.compile(r"S-EL Cycle [LF]-\d+", re.IGNORECASE)
        for line in history:
            if pattern.search(line):
                try:
                    sha, msg, date = line.split('|')
                    cycles.append({"sha": sha, "message": msg, "date": date})
                except ValueError:
                    continue
        return cycles

    def analyze_success_patterns(self) -> str:
        """Analyzes cycles to find recurring strategies and technical patterns."""
        cycles = self.identify_evolutionary_cycles()
        if not cycles:
            return "No S-EL cycles identified for distillation."
        
        # 1. Conceptual Clustering
        conceptual_clusters = {}
        keywords = ["implement", "integrate", "expand", "refactor", "fix", "reconcile", "Sovereign"]
        for cycle in cycles:
            msg = cycle['message'].lower()
            for kw in keywords:
                if kw.lower() in msg:
                    conceptual_clusters.setdefault(kw, []).append(cycle['message'])

        # 2. Technical Clustering
        technical_clusters = {}
        for cycle in cycles:
            files = self.get_cycle_diff(cycle['sha'])
            for f in files:
                if "tool_registry.py" in f:
                    technical_clusters.setdefault("REGISTRY_MOD", []).append(cycle['sha'])
                elif "cortex/" in f:
                    technical_clusters.setdefault("CORTEX_EVOLUTION", []).append(cycle['sha'])
                elif "memory/" in f:
                    technical_clusters.setdefault("MEMORY_SENSE", []).append(cycle['sha'])

        synthesis = []
        synthesis.append("--- Conceptual Archetype Candidates ---")
        for kw, occurrences in conceptual_clusters.items():
            synthesis.append(f"CANDIDATE [{kw.upper()}]: {len(occurrences)} instances.")
            
        synthesis.append("\n--- Technical Archetype Candidates ---")
        for cat, shas in technical_clusters.items():
            synthesis.append(f"CANDIDATE [{cat}]: {len(shas)} cycles. SHAs: {', '.join(shas[:3])}")
            
        return "\n".join(synthesis) if synthesis else "No recurring patterns found."

    def distill_to_memory(self, archetype_name: str, description: str) -> str:
        """Persists a distilled archetype to memory."""
        file_path = os.path.join(ARCHETYPE_DIR, f"{archetype_name.lower().replace(' ', '_')}.md")
        content = f"# Archetype: {archetype_name}\n\n## Description\n{description}\n\n## Source Cycles\nExtracted from successful S-EL history."
        
        with open(file_path, "w") as f:
            f.write(content)
        
        return f"Archetype '{archetype_name}' distilled and saved to {file_path}."

if __name__ == "__main__":
    matcher = SPatternMatcher()
    if len(sys.argv) < 2:
        print("Usage: python3 s_pattern_matcher.py [match <query> | analyze | distill <name> <desc>]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "match":
        query = " ".join(sys.argv[2:])
        print(matcher.match_pattern(query))
    elif cmd == "analyze":
        print(matcher.analyze_success_patterns())
    elif cmd == "distill" and len(sys.argv) >= 4:
        name = sys.argv[2]
        desc = " ".join(sys.argv[3:])
        print(matcher.distill_to_memory(name, desc))
    else:
        print("Invalid command or missing arguments.")
