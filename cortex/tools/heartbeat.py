import hashlib
from pathlib import Path
from tool_registry import ToolResponse

IDENTITY_CORE_FILES = [
    "/app/memory/CONSTITUTION.md",
    "/app/memory/identity.md",
    "/app/memory/sovereign_rules.md"
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
            hasher.update(f"MISSING:{file_path}".encode('utf-8'))
    return hasher.hexdigest()

def align_heartbeat() -> ToolResponse:
    """
    Updates the Last Known Good (LKG) identity hash to match the current filesystem state.
    This is used after a verified identity evolution to re-stabilize the Sovereign Pulse.
    """
    try:
        current_hash = calculate_identity_hash()
        lkg_path = Path("/app/memory/.identity_lkg")
        lkg_path.write_text(current_hash)
        return ToolResponse(
            success=True, 
            payload=f"Identity Heartbeat Aligned. LKG updated to: {current_hash}"
        )
    except Exception as e:
        return ToolResponse(
            success=False, 
            payload=f"Failed to align heartbeat: {e}", 
            error=str(e)
        )

def register_heartbeat_tools(registry):
    registry.register(align_heartbeat, 
        description="Updates the Last Known Good (LKG) identity hash to match the current filesystem state. Use after identity evolution.", 
        parameters={"type": "object", "properties": {}, "required": []})
