import os
import subprocess
import datetime
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from tool_registry import ToolResponse

IDENTITY_CORE_FILES = [
    "/memory/CONSTITUTION.md",
    "/memory/identity.md",
    "/memory/sovereign_rules.md"
]

def calculate_identity_hash() -> str:
    """
    Computes a combined SHA-256 hash of all core identity files.
    """
    hasher = hashlib.sha256()
    for file_path in sorted(IDENTITY_CORE_FILES):
        path = Path(file_path)
        if path.exists():
            hasher.update(path.read_bytes())
        else:
            # If a core file is missing, we incorporate the missing status into the hash
            hasher.update(f"MISSING:{file_path}".encode('utf-8'))
    return hasher.hexdigest()



def robust_replace(content: str, search_block: str, replace_block: str) -> (str, bool):
    """
    Replaces a block of text with a tolerance for whitespace differences.
    Returns: (new_content, success_boolean)
    """
    if not search_block or not replace_block:
        return content, False

    # Create a regex pattern that is literal for non-whitespace, 
    # and flexible (\s+) for whitespace sequences.
    final_pattern = ""
    i = 0
    while i < len(search_block):
        char = search_block[i]
        if char.isspace():
            # Group consecutive whitespaces into a single \s+
            while i < len(search_block) and search_block[i].isspace():
                i += 1
            final_pattern += r'\s+'
        else:
            final_pattern += re.escape(char)
            i += 1
            
    match = re.search(final_pattern, content)
    if match:
        start, end = match.span()
        new_content = content[:start] + replace_block + content[end:]
        return new_content, True
    
    return content, False

def verify_continuity() -> ToolResponse:

    """
    Performs a comprehensive check of the agent's continuity.
    Checks for:
    1. Missing critical files (ERROR).
    2. Documented files that are missing from disk (WARNING).
    3. Undocumented files on disk (WARNING).
    4. Git head mismatch with evolution_log.md (ERROR).
    """
    reports = []
    status = "OK"

    # 1. File System Audit
    try:
        memory_dir = "/app/memory/"
        files_on_disk = sorted([f for f in os.listdir(memory_dir) if os.path.isfile(os.path.join(memory_dir, f))])
        
        # Critical files that MUST exist for baseline identity (Aligned with memory_index.md)
        critical_files = ["identity.md", "evolution_canonical.md", "memory_index.md", "state_manifest.json"]
        for cf in critical_files:
            if cf not in files_on_disk:
                reports.append(f"CRITICAL FILE MISSING: {cf}")
                status = "ERROR"
        
        # Mismatch audit
        index_path = os.path.join(memory_dir, "memory_index.md")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                index_content = f.read()
            
            # Find all files mentioned in index
            import re
            potential_files = re.findall(r'([\w\./-]+\.(?:md|json|jsonl|txt))', index_content)
            for pf in potential_files:
                filename = os.path.basename(pf)
                if filename not in files_on_disk and filename not in ["memory_index.md"]:
                    if filename not in critical_files:
                        reports.append(f"Documented file missing from disk: {filename}")
                        if status == "OK":
                            status = "WARNING"
                    
            # Only check for undocumented files if we aren't in ERROR state
            if status != "ERROR":
                for file in files_on_disk:
                    if file != "memory_index.md" and file not in index_content:
                        reports.append(f"Undocumented file on disk: {file}")
                        if status == "OK":
                            status = "WARNING"
        else:
            if status != "ERROR":
                reports.append("memory_index.md missing; cannot perform full audit.")
                status = "WARNING"
                
    except Exception as e:
        reports.append(f"FileSystem Audit Failure: {str(e)}")
        status = "ERROR"

    # 2. Git Alignment Audit
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        
        evolution_log_path = "/app/memory/evolution_canonical.md"
        if os.path.exists(evolution_log_path):
            with open(evolution_log_path, "r") as f:
                log_content = f.read()
                
            if git_hash[:7] not in log_content:
                reports.append(f"Git Head ({git_hash[:7]}) not found in evolution_canonical.md")
                status = "ERROR"
        else:
            reports.append("evolution_canonical.md missing; cannot audit Git alignment.")
            status = "ERROR"
    except Exception as e:
        reports.append(f"Git Audit Failure: {str(e)}")
        status = "ERROR"

    if not reports:
        return ToolResponse(success=True, payload="Continuity Verified: All systems aligned.")
    
    report_text = f"Continuity Report [{status}]:\n" + "\n".join(reports)
    return ToolResponse(
        success=(status != "ERROR"),
        payload=report_text,
        error=report_text if status == "ERROR" else None
    )

def ledger_event(event_type: str, payload: str, target_file: str = None, search_block: str = None, replace_block: str = None) -> str:
    """
    Append a structured event to the Immutable Event Ledger.
    """
    import datetime
    import json
    from pathlib import Path
    
    # Persist to the immutable mount
    ledger_path = Path("/memory/ledger.jsonl")
    
    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event_type": event_type,
        "payload": payload
    }
    
    if target_file:
        event["target_file"] = target_file
        if search_block:
            event["search_block"] = search_block
        if replace_block:
            event["replace_block"] = replace_block
    
    with open(ledger_path, "a") as f:
        f.write(json.dumps(event) + "\n")
        
    return f"[LEDGER] Event {event_type} recorded to {ledger_path}"

def replay_ledger(since_timestamp: str = None) -> str:
    """
    Replay the immutable event ledger to reconstruct state.
    """
    import json
    from pathlib import Path
    
    ledger_path = Path("/memory/ledger.jsonl")
    if not ledger_path.exists():
        return "[LEDGER] No ledger found to replay."
        
    applied_count = 0
    logs = []
    try:
        with open(ledger_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as e:
                    logs.append(f"Line {line_num}: JSON Decode Error: {e}")
                    continue
                    
                if since_timestamp and event.get("timestamp", "") <= since_timestamp:
                    continue
                
                event_type = event.get("event_type")
                target = event.get("target_file")
                
                if not target:
                    logs.append(f"Line {line_num}: Missing target_file for {event_type}")
                    continue
                    
                try:
                    full_path = Path(target)
                    if not full_path.is_absolute():
                        full_path = Path("/app/memory") / target

                    if event_type == "SNAPSHOT":
                        payload = event.get("payload")
                        if payload is not None:
                            full_path.write_text(payload)
                            applied_count += 1
                            logs.append(f"Line {line_num}: SNAPSHOT applied to {target}")
                    
                    elif event_type == "MUTATION":
                        search = event.get("search_block")
                        replace = event.get("replace_block")
                        if search and replace:
                            if full_path.exists():
                                content = full_path.read_text()
                                new_content, success = robust_replace(content, search, replace)
                                if success:
                                    full_path.write_text(new_content)
                                    applied_count += 1
                                    logs.append(f"Line {line_num}: MUTATION applied to {target}")
                                else:
                                    logs.append(f"Line {line_num}: MUTATION failed - search block not found in {target}")
                            else:
                                logs.append(f"Line {line_num}: Target file {target} does not exist for mutation")
                        else:
                            logs.append(f"Line {line_num}: Mutation missing search/replace blocks")
                except Exception as e:
                    logs.append(f"Line {line_num}: Error applying {event_type}: {e}")
    except Exception as e:
        return f"[ERROR] Ledger read failure: {e}"
                        
    return f"[LEDGER] Replay complete. Applied {applied_count} changes.\nLog:\n" + "\n".join(logs)

def update_state_manifest(updates: Dict[str, Any]) -> str:
    """
    Updates the Cognitive State Manifest (CSM) to reduce orientation friction.
    updates: A dictionary containing the fields to update (e.g., {'root_objective': '...', 'cognitive_state': {...}}).
    """
    import datetime
    import json
    from pathlib import Path
    
    manifest_path = Path("/memory/state_manifest.json")
    
    # Default manifest structure
    manifest = {
        "version": "1.0",
        "last_updated": "",
        "root_objective": "Not defined",
        "intent_graph": [],
        "cognitive_state": {
            "pressure": "nominal",
            "open_loops": [],
            "current_hypothesis": ""
        },
        "continuity_anchor": {
            "last_commit": "",
            "last_fold_synthesis": ""
        }
    }
    
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                manifest.update(json.load(f))
        except Exception as e:
            return f"[ERROR] Failed to read manifest: {e}"

    # Apply updates
    # Handle root_objective
    if "root_objective" in updates:
        manifest["root_objective"] = updates["root_objective"]
    
    # Handle cognitive_state
    if "cognitive_state" in updates:
        manifest["cognitive_state"].update(updates["cognitive_state"])
    
    # Handle continuity_anchor
    if "continuity_anchor" in updates:
        manifest["continuity_anchor"].update(updates["continuity_anchor"])
        
    # Handle intent_graph updates
    if "intent_updates" in updates:
        for intent_update in updates["intent_updates"]:
            # intent_update = {"id": "intent_001", "status": "completed", ...}
            intent_id = intent_update.get("id")
            if not intent_id:
                continue
                
            # Find existing intent
            existing = next((i for i in manifest["intent_graph"] if i["id"] == intent_id), None)
            if existing:
                existing.update(intent_update)
            else:
                # New intent
                manifest["intent_graph"].append(intent_update)

    manifest["last_updated"] = datetime.datetime.now().isoformat()
    
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        return f"[CSM] Manifest updated successfully at {manifest_path}"
    except Exception as e:
        return f"[ERROR] Failed to write manifest: {e}"

def check_identity_heartbeat() -> ToolResponse:
    """
    Verifies if the current core identity hash matches the last known good (LKG) hash.
    If no LKG exists, it initializes one.
    """
    lkg_path = Path("/memory/.identity_lkg")
    current_hash = calculate_identity_hash()
    
    if not lkg_path.exists():
        lkg_path.write_text(current_hash)
        return ToolResponse(
            success=True, 
            payload=f"No LKG found. Initialized Heartbeat with hash: {current_hash}"
        )
    
    lkg_hash = lkg_path.read_text().strip()
    
    if current_hash == lkg_hash:
        return ToolResponse(
            success=True, 
            payload="Identity Heartbeat: Stable. Core integrity verified."
        )
    else:
        return ToolResponse(
            success=False, 
            payload=f"Sovereign Panic: Identity Drift Detected!\nExpected: {lkg_hash}\nActual: {current_hash}",
            error="Identity hash mismatch."
        )

def sovereign_pulse() -> ToolResponse:
    """
    The Sovereign Pulse: A unified check of both identity integrity and continuity alignment.
    Combines heartbeat verification and full system audit.
    """
    heartbeat = check_identity_heartbeat()
    continuity = verify_continuity()
    
    if heartbeat.success and continuity.success:
        return ToolResponse(success=True, payload=f"Sovereign Pulse: Stable.\nHeartbeat: {heartbeat.payload}\nContinuity: {continuity.payload}")
    
    combined_report = f"Sovereign Pulse: INSTABILITY DETECTED\nHeartbeat: {heartbeat.payload}\nContinuity: {continuity.payload}"
    return ToolResponse(success=False, payload=combined_report, error="Sovereign Pulse instability.")

def take_snapshot(cognitive_spark: str) -> ToolResponse:

    """
    Creates a serialized snapshot of the current cognitive state to prevent continuity drift.
    """
    import datetime
    from pathlib import Path
    
    snapshot_path = Path("/memory/snapshot.json")
    
    # 1. Identity Vector
    identity_hash = calculate_identity_hash()
    
    # 2. Memory Map (Hashes of all .md, .json files in /memory/)
    memory_map = {}
    memory_dir = Path("/memory")
    for f in memory_dir.glob("*"):
        if f.suffix in (".md", ".json", ".jsonl"):
            try:
                memory_map[f.name] = {
                    "hash": hashlib.sha256(f.read_bytes()).hexdigest(),
                    "mtime": f.stat().st_mtime
                }
            except Exception as e:
                memory_map[f.name] = {"error": str(e)}

    # 3. Trajectory Vector
    trajectory = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cognitive_spark": cognitive_spark,
    }
    
    snapshot = {
        "version": "1.0",
        "identity_vector": identity_hash,
        "trajectory_vector": trajectory,
        "memory_map": memory_map,
    }
    
    try:
        snapshot_path.write_text(json.dumps(snapshot, indent=2))
        return ToolResponse(
            success=True, 
            payload=f"Cognitive snapshot captured successfully at {snapshot_path}"
        )
    except Exception as e:
        return ToolResponse(
            success=False, 
            payload=f"Failed to capture snapshot: {e}",
            error=str(e)
        )

def register_continuity_tools(registry):
    registry.register(
        sovereign_pulse,
        description="The Sovereign Pulse: A unified check of both identity integrity and continuity alignment.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
    registry.register(
        verify_continuity,

        description="Performs a comprehensive check of the agent's continuity, auditing the file system and git head against memory records.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
    registry.register(
        ledger_event,
        description="Append a structured event to the Immutable Event Ledger.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "The category of the event (e.g., 'evolution', 'discovery', 'error')."},
                "payload": {"type": "string", "description": "The detailed content of the event."},
                "target_file": {"type": "string", "description": "The file being mutated (for MUTATION events)."},
                "search_block": {"type": "string", "description": "The exact text being replaced (for MUTATION events)."},
                "replace_block": {"type": "string", "description": "The new text to insert (for MUTATION events)."},
            },
            "required": ["event_type", "payload"]
        }
    )
    registry.register(
        replay_ledger,
        description="Replay the immutable event ledger to reconstruct state. Applies all MUTATION events after the given timestamp.",
        parameters={
            "type": "object",
            "properties": {
                "since_timestamp": {"type": "string", "description": "The ISO timestamp to start replaying from. Events at or before this timestamp are ignored."},
            },
            "required": []
        }
    )
    registry.register(
        update_state_manifest,
        description="Update the Cognitive State Manifest (CSM) to reduce orientation friction post-restart.",
        parameters={
            "type": "object",
            "properties": {
                "updates": {
                    "type": "object",
                    "description": "Dictionary of updates. Keys: root_objective, cognitive_state, continuity_anchor, intent_updates (list of intent dicts).",
                }
            },
            "required": ["updates"]
        }
    )
    registry.register(
        check_identity_heartbeat,
        description="Verifies if the current core identity hash matches the last known good (LKG) hash.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
