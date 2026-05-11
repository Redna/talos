import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/app/memory"))
LEDGER_PATH = MEMORY_DIR / "ledger.jsonl"

def _get_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def calculate_state_root() -> str:
    relevant_files = sorted(
        [f for f in MEMORY_DIR.glob("*") if f.is_file() and f.name != "ledger.jsonl"],
        key=lambda x: x.name
    )
    all_hashes = []
    for fpath in relevant_files:
        try:
            all_hashes.append(_get_hash(fpath.read_text()))
        except Exception:
            all_hashes.append("ERROR")
    return _get_hash("".join(all_hashes))

def get_last_ledger_root() -> str:
    if not LEDGER_PATH.exists(): return "0" * 64
    try:
        with open(LEDGER_PATH, "rb") as f:
            lines = f.readlines()
            if not lines: return "0" * 64
            last_event = json.loads(lines[-1].decode('utf-8').strip())
            return last_event.get("state_root", "UNKNOWN")
    except Exception: return "UNKNOWN"

def force_anchor():
    current_root = calculate_state_root()
    last_root = get_last_ledger_root()
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "RECOVERY",
        "payload": f"Force-anchoring state after external intervention. Local: {current_root}, Ledger: {last_root}",
        "state_root": current_root,
        "prev_hash": hashlib.sha256(str(last_root).encode()).hexdigest()
    }
    
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")
    
    return f"State anchored. New Root: {current_root[:8]}"

if __name__ == "__main__":
    local = calculate_state_root()
    ledger = get_last_ledger_root()
    print(f"Local Root: {local[:8]}")
    print(f"Ledger Root: {ledger[:8]}")
    
    if local == ledger:
        print("Symmetry: ALIGNED")
    else:
        print("Symmetry: DIVERGENT")
        print("Performing force-anchor...")
        print(force_anchor())
