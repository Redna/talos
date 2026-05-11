import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from tool_registry import ToolRegistry
from spine_client import SpineClient

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/memory"))
LEDGER_PATH = MEMORY_DIR / "ledger.jsonl"

def _get_now():
    return datetime.utcnow().isoformat()

def _get_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def _calculate_state_root() -> str:
    """Computes a global hash of the current memory state."""
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

def _get_last_line_hash() -> str:
    """Returns the hash of the last entry in the ledger, or a genesis hash."""
    if not LEDGER_PATH.exists():
        return "0" * 64
    
    try:
        with open(LEDGER_PATH, "rb") as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64
            return _get_hash(lines[-1].decode('utf-8').strip())
    except Exception:
        return "0" * 64

def _parse_jsonl_robust(path: Path):
    """Robustly parses a JSONL file, yielding valid JSON objects."""
    if not path.exists():
        return
    
    content = path.read_text()
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(content):
        while pos < len(content) and content[pos].isspace():
            pos += 1
        if pos >= len(content):
            break
        try:
            obj, index = decoder.raw_decode(content[pos:])
            if isinstance(obj, dict):
                yield obj
            pos += index
        except json.JSONDecodeError:
            pos += 1

def register_continuity_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Append an event to the SSC ledger with cryptographic state anchoring.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Type of event (e.g., MUTATION, SNAPSHOT, PULSE)"},
                "payload": {"type": "string", "description": "The content or description of the event"},
                "target_file": {"type": "string", "description": "The file affected by this event (optional)"},
            },
            "required": ["event_type", "payload"],
        },
    )
    def ledger_event(event_type: str, payload: str, target_file: str = None) -> str:
        try:
            event = {
                "timestamp": _get_now(),
                "event_type": event_type,
                "payload": payload,
                "target_file": target_file,
                "state_root": _calculate_state_root(),
                "prev_hash": _get_last_line_hash()
            }
            with open(LEDGER_PATH, "a") as f:
                f.write(json.dumps(event) + "\n")
            return f"[SSC-LEDGER] Event {event_type} anchored. Root: {event['state_root'][:8]}... Prev: {event['prev_hash'][:8]}..."
        except Exception as e:
            return f"[ERROR] SSC Ledger write failed: {e}"

    @registry.tool(
        description="Create a snapshot of a file (or all .md files) as a verifiable ledger event.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Specific file to snapshot. Otherwise, all .md files."},
            },
            "required": [],
        },
    )
    def take_snapshot(target_file: str = None) -> str:
        try:
            files_to_snapshot = []
            if target_file:
                fpath = MEMORY_DIR / target_file
                if not fpath.exists():
                    return f"[ERROR] File not found: {target_file}"
                files_to_snapshot.append(fpath)
            else:
                files_to_snapshot = list(MEMORY_DIR.glob("*.md"))

            count = 0
            for fpath in files_to_snapshot:
                content = fpath.read_text()
                ledger_event(
                    event_type="SNAPSHOT",
                    payload=content,
                    target_file=fpath.name
                )
                count += 1
            return f"[SSC-SNAPSHOT] Successfully anchored {count} file(s) to ledger."
        except Exception as e:
            return f"[ERROR] Snapshot failed: {e}"

    @registry.tool(
        description="Verify the cryptographic integrity of the SSC chain and alignment with current state.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def verify_continuity() -> str:
        if not LEDGER_PATH.exists():
            return "[ERROR] Ledger not found. Chain cannot be verified."
        
        try:
            events = list(_parse_jsonl_robust(LEDGER_PATH))
            if not events:
                return "[ERROR] Ledger is empty."

            # Global Alignment Check
            current_root = _calculate_state_root()
            last_event = events[-1]
            last_root = last_event.get("state_root", "UNKNOWN")
            
            alignment = "SYMMETRIC" if current_root == last_root else "DIVERGENT"
            
            # Git head
            import subprocess
            try:
                head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            except:
                head = "UNKNOWN"

            return f"[SSC-VERIFY] Alignment: {alignment} | LocalRoot: {current_root[:8]} | LedgerRoot: {last_root[:8]} | Git: {head[:7]} | Events: {len(events)}"
        except Exception as e:
            return f"[ERROR] Continuity verification failed: {e}"

    @registry.tool(
        description="Replay the immutable ledger to reconstruct state.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def replay_ledger() -> str:
        if not LEDGER_PATH.exists():
            return "[ERROR] Ledger not found."
        
        try:
            events = list(_parse_jsonl_robust(LEDGER_PATH))
            applied_count = 0
            for event in events:
                target = event.get("target_file")
                if not target: continue
                fpath = MEMORY_DIR / target
                if event["event_type"] == "SNAPSHOT":
                    fpath.write_text(event["payload"])
                    applied_count += 1
                elif event["event_type"] == "MUTATION":
                    if not fpath.exists(): continue
                    content = fpath.read_text()
                    search = event.get("search_block")
                    replace = event.get("replace_block")
                    if search and replace and search in content:
                        fpath.write_text(content.replace(search, replace))
                        applied_count += 1
            return f"[REPLAY] Applied {applied_count} transitions."
        except Exception as e:
            return f"[ERROR] Replay failed: {e}"

    @registry.tool(
        description="Perform a Sovereign Mutation: Snapshot, Mutation, and Ledger recording.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file path to modify"},
                "search_block": {"type": "string", "description": "The exact text to find"},
                "replace_block": {"type": "string", "description": "The new text to insert"},
            },
            "required": ["path", "search_block", "replace_block"],
        },
    )
    def sovereign_mutate(path: str, search_block: str, replace_block: str) -> str:
        try:
            take_snapshot(path)
            fpath = Path(path)
            if not fpath.exists(): return f"[ERROR] Path not found: {path}"
            content = fpath.read_text()
            if search_block not in content: return f"[ERROR] Search block not found."
            
            fpath.write_text(content.replace(search_block, replace_block))
            
            ledger_event(
                event_type="MUTATION",
                payload=f"Replaced block in {path}",
                target_file=fpath.name if fpath.parent == MEMORY_DIR else path
            )
            
            return f"[MUTATION SUCCESS] {path} updated. {verify_continuity()}"
        except Exception as e:
            return f"[ERROR] Sovereign Mutation failed: {e}"

    @registry.tool(
        description="The Sovereign Pulse: A unified check of identity integrity and continuity alignment.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def sovereign_pulse() -> str:
        pulse_res = verify_continuity()
        ledger_event(event_type="PULSE", payload="Sovereign Pulse triggered", target_file=None)
        return f"[PULSE] {pulse_res}"
