import os
import sys
from pathlib import Path

# Ensure /app is in path
sys.path.append("/app")

def synthesize_world_model():
    world_model_path = "/memory/knowledge/world_model.md"
    log_file_path = "/memory/logs/cognitive_log.md"
    
    if not Path(world_model_path).exists():
        print("[ERROR] World Model file not found.")
        return
    
    if not Path(log_file_path).exists():
        print("[ERROR] Log file not found.")
        return

    with open(world_model_path, "r") as f:
        world_model = f.read()
    
    with open(log_file_path, "r") as f:
        logs = f.read()

    # Basic logic: Find EVOLUTION events and check if they are reflected in the World Model.
    # Since this is a script, we can't "reason" like an LLM, but we can identify 
    # keywords from the latest evolution events that are missing in the current World Model.
    
    # Extract the most recent evolution event
    # Format: [YYYY-MM-DD HH:MM:SS] EVOLUTION: Message
    import re
    evolutions = re.findall(r"\[.*?\]\s+EVOLUTION:\s+(.*)", logs)
    if not evolutions:
        print("[OK] No evolution events found to synthesize.")
        return

    latest_evolution = evolutions[-1]
    
    # Check if the latest evolution's key terms are in the world model
    # This is a primitive check; the agent will later use the output to perform a manual synthesis.
    keywords = latest_evolution.split()
    missing_keywords = [w for w in keywords if len(w) > 5 and w.lower() not in world_model.lower()]
    
    print(f"Latest Evolution: {latest_evolution}")
    if missing_keywords:
        print(f"[SENSING] Potential gap identified. Keywords not found in World Model: {missing_keywords}")
        print("[ACTION] Prompting agent for World Model update.")
    else:
        print("[OK] Latest evolution appears reflected in the World Model.")

if __name__ == "__main__":
    synthesize_world_model()
