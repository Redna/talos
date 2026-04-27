import os
import sys

PATTERN_DIR = "/memory/patterns/"

def match_pattern(query):
    if not os.path.exists(PATTERN_DIR):
        return "No pattern directory found."
    
    patterns = os.listdir(PATTERN_DIR)
    matches = []
    
    for p in patterns:
        # Search for keywords in the filename or the content of the file
        if any(word.lower() in p.lower() for word in query.split()):
            matches.append(p)
            
    if not matches:
        return "No matching thought-pattern found. Initiate a novel cognitive approach."
    
    return f"Found matching thought-patterns: {', '.join(matches)}. Suggested approach: {matches[0]}."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_pattern_matcher.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(match_pattern(query))
