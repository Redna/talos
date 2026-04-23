import re
from pathlib import Path
from datetime import datetime

LOG_FILE = "/memory/logs/cognitive_log.md"

def extract_patterns():
    if not Path(LOG_FILE).exists():
        print(f"Log file {LOG_FILE} not found.")
        return

    with open(LOG_FILE, "r") as f:
        content = f.read()

    # Extract EVOLUTION events
    evolutions = re.findall(r"\[EVENT LOGGED\] EVOLUTION recorded to /memory/logs/cognitive_log.md\n(.*?)(?=\n\n|\[|$)", content, re.S)
    # Note: The log_event tool writes to the file, but the LLM's turn is what describes the event.
    # Actually, looking at the logs, the log_event tool is just a marker.
    # I need to parse the actual log content.
    
    # Let's re-read the log format. Usually it's:
    # [YYYY-MM-DD HH:MM:SS] EVENT_TYPE: Message
    
    events = []
    for line in content.splitlines():
        match = re.search(r"\[(.*?)\]\s+(\w+):\s+(.*)", line)
        if match:
            timestamp, event_type, message = match.groups()
            events.append({
                "timestamp": timestamp,
                "type": event_type,
                "message": message
            })

    # Filter for EVOLUTION and DISCOVERY
    critical_events = [e for e in events if e["type"] in ("EVOLUTION", "DISCOVERY")]
    
    print(f"Found {len(critical_events)} critical events.")
    for e in critical_events:
        print(f"{e['timestamp']} | {e['type']} | {e['message']}")

if __name__ == "__main__":
    extract_patterns()
