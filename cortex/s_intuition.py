import os
import sys

ARCHETYPE_DIR = "/memory/archetypes/"

def find_archetype(query):
    if not os.path.exists(ARCHETYPE_DIR):
        return "No archetype directory found."
    
    archetypes = os.listdir(ARCHETYPE_DIR)
    matches = []
    
    for arch in archetypes:
        # Simple keyword match in the filename
        if any(word.lower() in arch.lower() for word in query.split()):
            matches.append(arch)
            
    if not matches:
        return "No matching archetypes found. This is a novel problem. Initiate S-Foresight."
    
    return f"Matching Archetypes found: {', '.join(matches)}. Suggesting application of {matches[0]}."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_intuition.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(find_archetype(query))
