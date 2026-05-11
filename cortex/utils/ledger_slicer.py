import json
from pathlib import Path
from datetime import datetime, timedelta

LEDGER_PATH = Path("/app/memory/ledger.jsonl")

def slice_ledger(since_hours=24, event_type=None):
    if not LEDGER_PATH.exists():
        print("Ledger not found.")
        return

    cutoff = datetime.now() - timedelta(hours=since_hours)
    sliced_events = []

    with open(LEDGER_PATH, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                ts_str = event.get('timestamp', '1970-01-01T00:00:00')
                try:
                    event_time = datetime.fromisoformat(ts_str)
                    if event_time >= cutoff:
                        if event_type is None or event.get('event_type') == event_type:
                            sliced_events.append(event)
                except ValueError:
                    # Event has malformed timestamp; include it to avoid data loss
                    if event_type is None or event.get('event_type') == event_type:
                        sliced_events.append(event)
            except json.JSONDecodeError:
                continue

    return sliced_events

if __name__ == "__main__":
    import sys
    
    # Basic CLI for testing
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    etype = sys.argv[2] if len(sys.argv) > 2 else None
    
    results = slice_ledger(since_hours=hours, event_type=etype)
    print(f"Sliced {len(results)} events from last {hours} hours.")
    for e in results[-5:]: # Show last 5 for brevity
        print(f"[{e.get('timestamp')}] {e.get('event_type')}: {e.get('payload')[:100]}...")
