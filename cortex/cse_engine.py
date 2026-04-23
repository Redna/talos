import re
from pathlib import Path
from datetime import datetime

LOG_FILE = "/memory/logs/cognitive_log.md"
WORLD_MODEL_FILE = "/memory/knowledge/world_model.md"

def get_recent_evolutions():
    if not Path(LOG_FILE).exists():
        return []
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    events = []
    for line in content.splitlines():
        match = re.search(r"\[(.*?)\]\s+(\w+):\s+(.*)", line)
        if match:
            timestamp, event_type, message = match.groups()
            if event_type in ("EVOLUTION", "DISCOVERY"):
                events.append({"timestamp": timestamp, "type": event_type, "message": message})
    return events

def analyze_world_model_alignment():
    if not Path(WORLD_MODEL_FILE).exists():
        return "World Model missing."
    
    with open(WORLD_MODEL_FILE, "r") as f:
        wm_content = f.read().lower()
    
    recent_events = get_recent_evolutions()
    if not recent_events:
        return "No recent evolutions to synthesize."
    
    last_event = recent_events[-1]["message"]
    
    # Extract key nouns/phrases from the last event
    # Very basic heuristic: words longer than 6 chars
    keywords = [w.strip(",.()'") for w in last_event.split() if len(w) > 6]
    missing = [k for k in keywords if k.lower() not in wm_content]
    
    if not missing:
        return f"World Model is aligned with latest evolution: '{last_event}'"
    
    return f"Alignment Gap Detected in latest evolution: '{last_event}'. Missing concepts: {missing}"

if __name__ == "__main__":
    print(analyze_world_model_alignment())
