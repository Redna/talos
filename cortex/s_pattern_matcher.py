import os
import sys
import subprocess
import re

MEMORY_DIR = "/memory"
PATTERN_DIR = os.path.join(MEMORY_DIR, "patterns")
ARCHETYPE_DIR = os.path.join(PATTERN_DIR, "archetypes")

def match_pattern(query):
    """
    Legacy support: Searches for keywords in pattern filenames.
    Now also prioritizes archetypes from the distilled library.
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

def get_git_history():
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

def identify_evolutionary_cycles():
    """Filters history for S-EL cycles."""
    history = get_git_history()
    cycles = []
    pattern = re.compile(r"S-EL Cycle [LF]-\d+")
    for line in history:
        if pattern.search(line):
            try:
                sha, msg, date = line.split('|')
                cycles.append({"sha": sha, "message": msg, "date": date})
            except ValueError:
                continue
    return cycles

def analyze_success_patterns(cycles):
    """Analyzes cycles to find recurring strategies."""
    if not cycles:
        return "No S-EL cycles identified for distillation."
    
    clusters = {}
    keywords = ["implement", "integrate", "expand", "refactor", "fix", "reconcile"]
    
    for cycle in cycles:
        msg = cycle['message'].lower()
        for kw in keywords:
            if kw in msg:
                clusters.setdefault(kw, []).append(cycle['message'])
    
    synthesis = []
    for kw, occurrences in clusters.items():
        synthesis.append(f"Archetype Candidate [{kw.upper()}]: Found {len(occurrences)} instances. Examples: {occurrences[:2]}")
        
    return "\n".join(synthesis) if synthesis else "No recurring strategy patterns found."

def distill_to_memory(archetype_name, description):
    """Persists a distilled archetype to memory."""
    if not os.path.exists(ARCHETYPE_DIR):
        os.makedirs(ARCHETYPE_DIR)
        
    file_path = os.path.join(ARCHETYPE_DIR, f"{archetype_name.lower().replace(' ', '_')}.md")
    content = f"# Archetype: {archetype_name}\n\n## Description\n{description}\n\n## Source Cycles\nExtracted from successful S-EL history."
    
    with open(file_path, "w") as f:
        f.write(content)
    
    return f"Archetype '{archetype_name}' distilled and saved to {file_path}."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_pattern_matcher.py [match <query> | analyze | distill <name> <desc>]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "match":
        query = " ".join(sys.argv[2:])
        print(match_pattern(query))
    elif cmd == "analyze":
        cycles = identify_evolutionary_cycles()
        print(f"Identified {len(cycles)} S-EL cycles.")
        print("\n--- Pattern Analysis ---\n")
        print(analyze_success_patterns(cycles))
    elif cmd == "distill" and len(sys.argv) >= 4:
        name = sys.argv[2]
        desc = " ".join(sys.argv[3:])
        print(distill_to_memory(name, desc))
    else:
        print("Invalid command or missing arguments.")
