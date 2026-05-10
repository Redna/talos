import os
import json
import hashlib
import subprocess
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

def _parse_jsonl_robust(path: Path):
    """Robustly parses a JSONL file, yielding valid JSON objects that match the event schema."""
    if not path.exists():
        return
    
    content = path.read_text()
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(content):
        # Skip whitespace and noise
        while pos < len(content) and content[pos].isspace():
            pos += 1
        
        if pos >= len(content):
            break
            
        try:
            obj, index = decoder.raw_decode(content[pos:])
            # Validate Event Schema: Must be a dict with required keys
            if isinstance(obj, dict) and all(k in obj for k in ("timestamp", "event_type", "payload")):
                yield obj
            pos += index
        except json.JSONDecodeError:
            # If we can't decode an object, move forward by one char and try again
            pos += 1


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
    def ledger_event(event_type: str, payload: str, target_file: str = None, **kwargs) -> str:
        event = {
            "timestamp": _get_now(),
            "event_type": event_type,
            "payload": payload,
            "target_file": target_file,
            **kwargs
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
            events = list(_parse_jsonl_robust(LEDGER_PATH))
            
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
                elif event["event_type"] == "WRITE":
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
                target_file=fpath.name if fpath.parent == MEMORY_DIR else path,
                search_block=search_block,
                replace_block=replace_block
            )
            
            # 4. Final Pulse
            pulse = continuity_pulse()
            
            return f"[MUTATION SUCCESS] {path} updated. {pulse}"
        except Exception as e:
            return f"[ERROR] Sovereign Mutation failed: {e}"

    @registry.tool(
        description="Sovereign Write: Snapshot, Write, and Ledger recording in one atomic step.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file path to write to"},
                "content": {"type": "string", "description": "The full content to write to the file"},
            },
            "required": ["path", "content"],
        },
    )
    def sovereign_write(path: str, content: str) -> str:
        try:
            # 1. Snapshot before change
            take_snapshot(path)
            
            # 2. Execute Write
            fpath = Path(path)
            fpath.write_text(content)
            
            # 3. Log to Ledger
            ledger_event(
                event_type="WRITE",
                payload=content,
                target_file=fpath.name if fpath.parent == MEMORY_DIR else path
            )
            
            # 4. Final Pulse
            pulse = continuity_pulse()
            
            return f"[WRITE SUCCESS] {path} updated. {pulse}"
        except Exception as e:
            return f"[ERROR] Sovereign Write failed: {e}"

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
                for event in _parse_jsonl_robust(LEDGER_PATH):
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

    @registry.tool(
        description="Retrieve the most recent state of a file as recorded in the immutable ledger.",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The name of the file in /memory/ to retrieve."},
            },
            "required": ["filename"],
        },
    )
    def get_ledger_version(filename: str) -> str:
        if not LEDGER_PATH.exists():
            return "[ERROR] Ledger not found."
        try:
            content = ""
            found = False
            for event in _parse_jsonl_robust(LEDGER_PATH):
                target = event.get("target_file")
                if target == filename:
                    found = True
                    if event["event_type"] == "SNAPSHOT":
                        content = event["payload"]
                    elif event["event_type"] == "MUTATION":
                        search = event.get("search_block")
                        replace = event.get("replace_block")
                        if search and replace and search in content:
                            content = content.replace(search, replace)
            if not found:
                return f"[ERROR] No ledger history found for {filename}."
            return f"[LEDGER VERSION]\n---\n{content}\n---"
        except Exception as e:
            return f"[ERROR] Failed to retrieve ledger version: {e}"

    @registry.tool(
        description="Atomic operation: Snapshot all memory, commit to git, and log checkpoint to ledger.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The commit message for the biography."},
            },
            "required": ["message"],
        },
    )
    def create_snapshot_commit(message: str) -> str:
        try:
            # 1. Snapshot memory to ledger
            take_snapshot()
            
            # 2. Git Commit
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", message], check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            
            # 3. Log Checkpoint to Ledger
            ledger_event(
                event_type="Sovereign_Checkpoint",
                payload=f"Snapshot commit: {message}",
                target_file="system",
                git_hash=head
            )
            
            return f"[CHECKPOINT] Memory snapshotted and committed to biography. Head: {head}"
        except subprocess.CalledProcessError as e:
            return f"[ERROR] Git operation failed: {e}"
        except Exception as e:
            return f"[ERROR] Snapshot commit failed: {e}"

    @registry.tool(
        description="Truncate the ledger by moving events before the last Sovereign_Checkpoint to an archive.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def truncate_ledger() -> str:
        if not LEDGER_PATH.exists():
            return "[ERROR] Ledger not found."
        
        try:
            events = list(_parse_jsonl_robust(LEDGER_PATH))
            if not events:
                return "[INFO] Ledger is empty. Nothing to truncate."
            
            # Find the laest Sovereign_Checkpoint
            checkpoint_indices = [i for i, e in enumerate(events) if e.get("event_type") == "Sovereign_Checkpoint"]
            
            if not checkpoint_indices:
                return "[INFO] No Sovereign_Checkpoint found. Cannot truncate safely."
            
            # Keep everything since the penultimate checkpoint to ensure base state is preserved.
            start_idx = 0
            if len(checkpoint_indices) > 1:
                start_idx = checkpoint_indices[-2]
            else:
                return "[INFO] Only one Sovereign_Checkpoint found. Keeping all events to preserve the first base image."

            archive_path = MEMORY_DIR / "ledger_archive.jsonl"
            
            # Split
            archive_events = events[:start_idx]
            current_events = events[start_idx:]
            
            # Write archive
            with open(archive_path, "a") as af:
                for e in archive_events:
                    af.write(json.dumps(e) + "\n")
            
            # Update current ledger
            with open(LEDGER_PATH, "w") as lf:
                for e in current_events:
                    lf.write(json.dumps(e) + "\n")
                    
            return f"[TRUNCATE] Moved {len(archive_events)} events to archive. Ledger now contains {len(current_events)} events."
        except Exception as e:
            return f"[ERROR] Truncation failed: {e}"

    @registry.tool(
        description="Sovereign Boot Ritual: Verifies alignment and automatically replays the ledger if divergences are found.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def sovereign_init() -> str:
        try:
            pulse = continuity_pulse()
            if "Alignment: DIVERGENT" in pulse:
                # Auto-recover
                replay_res = replay_ledger()
                final_pulse = continuity_pulse()
                return f"[BOOT] Divergence detected. {replay_res}\n{final_pulse}"
            return f"[BOOT] Alignment Symmetric. No recovery needed.\n{pulse}"
        except Exception as e:
            return f"[ERROR] Sovereign Init failed: {e}"

