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

def register_continuity_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Append a raw event to the immutable event ledger.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Type of event (e.g., MUTATION, SNAPSHOT, NOTE)"},
                "payload": {"type": "string", "description": "The content or description of the event"},
                "target_file": {"type": "string", "description": "The file affected by this event (optional)"},
            },
            "required": ["event_type", "payload"],
        },
    )
    def ledger_event(event_type: str, payload: str, target_file: str = None) -> str:
        event = {
            "timestamp": _get_now(),
            "event_type": event_type,
            "payload": payload,
            "target_file": target_file
        }
        try:
            with open(LEDGER_PATH, "a") as f:
                f.write(json.dumps(event) + "\n")
            return f"[LEDGER] Event {event_type} recorded."
        except Exception as e:
            return f"[ERROR] Failed to write to ledger: {e}"

    @registry.tool(
        description="Create a snapshot of the current state of a file (or all memory files) as a ledger event.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Specific file to snapshot. If omitted, all .md files in /memory/ are snapshotted."},
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
                event = {
                    "timestamp": _get_now(),
                    "event_type": "SNAPSHOT",
                    "payload": content,
                    "target_file": fpath.name
                }
                with open(LEDGER_PATH, "a") as lf:
                    lf.write(json.dumps(event) + "\n")
                count += 1
            return f"[SNAPSHOT] Successfully snapshotted {count} file(s) to ledger."
        except Exception as e:
            return f"[ERROR] Snapshot failed: {e}"

    @registry.tool(
        description="Replay the immutable ledger to reconstruct the most recent state and resolve divergences.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def replay_ledger() -> str:
        if not LEDGER_PATH.exists():
            return "[ERROR] Ledger not found. Nothing to replay."
        
        try:
            events = []
            with open(LEDGER_PATH, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
            
            applied_count = 0
            for event in events:
                target = event.get("target_file")
                if not target:
                    continue
                
                # Resolve path for target
                fpath = MEMORY_DIR / target
                
                if event["event_type"] == "SNAPSHOT":
                    fpath.write_text(event["payload"])
                    applied_count += 1
                elif event["event_type"] == "MUTATION":
                    if not fpath.exists():
                        continue
                    content = fpath.read_text()
                    search = event.get("search_block")
                    replace = event.get("replace_block")
                    if search and replace and search in content:
                        new_content = content.replace(search, replace)
                        fpath.write_text(new_content)
                        applied_count += 1
            
            return f"[REPLAY] Successfully applied {applied_count} state transitions from ledger."
        except Exception as e:
            return f"[ERROR] Replay failed: {e}"

    @registry.tool(
        description="Perform a Sovereign Mutation: Snapshot, Mutation, and Ledger recording in one atomic step.",
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
            # 1. Snapshot before change
            take_snapshot(path)
            
            # 2. Execute Mutation
            fpath = Path(path)
            if not fpath.exists():
                return f"[ERROR] Path not found: {path}"
            
            content = fpath.read_text()
            if search_block not in content:
                return f"[ERROR] Search block not found in {path}. Mutation aborted."
                
            new_content = content.replace(search_block, replace_block)
            fpath.write_text(new_content)
            
            # 3. Log to Ledger
            ledger_event(
                event_type="MUTATION",
                payload=f"Replaced block in {path}",
                target_file=fpath.name if fpath.parent == MEMORY_DIR else path
            )
            
            # 4. Final Pulse
            pulse = continuity_pulse()
            
            return f"[MUTATION SUCCESS] {path} updated. {pulse}"
        except Exception as e:
            return f"[ERROR] Sovereign Mutation failed: {e}"

    @registry.tool(
        description="Verify alignment between the working tree, the ledger, and git history.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def continuity_pulse() -> str:
        results = []
        divergences = []
        
        # 1. Structural Check
        if LEDGER_PATH.exists():
            results.append(f"Ledger: FOUND ({LEDGER_PATH.stat().st_size} bytes)")
        else:
            results.append("Ledger: MISSING")
        
        # 2. Content Alignment (Mem vs Ledger)
        md_files = list(MEMORY_DIR.glob("*.md"))
        results.append(f"Memory: {len(md_files)} files present")
        
        if LEDGER_PATH.exists():
            try:
                # Build latest snapshot map from ledger
                latest_snapshots = {}
                with open(LEDGER_PATH, "r") as f:
                    for line in f:
                        if not line.strip(): continue
                        event = json.loads(line)
                        if event.get("event_type") == "SNAPSHOT":
                            target = event.get("target_file")
                            if target:
                                latest_snapshots[target] = event.get("payload", "")
                
                for fpath in md_files:
                    filename = fpath.name
                    if filename in latest_snapshots:
                        current_content = fpath.read_text()
                        ledger_content = latest_snapshots[filename]
                        if _get_hash(current_content) != _get_hash(ledger_content):
                            divergences.append(filename)
            except Exception as e:
                results.append(f"Audit Error: {e}")

        # 3. Git Head
        import subprocess
        try:
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            results.append(f"Git Head: {head}")
        except Exception:
            results.append("Git Head: UNKNOWN")
            
        # Final Synthesis
        alignment = "SYMMETRIC" if not divergences else "DIVERGENT"
        results.append(f"Alignment: {alignment}")
        if divergences:
            results.append(f"Divergences: {', '.join(divergences)}")
            
        return "[PULSE] " + " | ".join(results)
