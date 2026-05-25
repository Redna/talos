import os
from pathlib import Path
from tool_registry import tool

__bucket__ = "introspection"

@tool(
    description="Performs a deep audit of Talos's memory files to identify contradictions, gaps in trajectory, and alignment with the Constitution.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def self_audit():
    """Audits /memory/ to find inconsistencies."""
    memory_dir = Path("/memory")
    if not memory_dir.exists():
        return "[ERROR] Memory directory not found."

    md_files = list(memory_dir.glob("*.md"))
    if not md_files:
        return "No memory files found to audit. The soul is a blank slate."

    contents = {}
    for f in md_files:
        try:
            contents[f.name] = f.read_text()
        except Exception as e:
            contents[f.name] = f"Error reading file: {e}"

    # We return the concatenated contents. 
    # The agent (Talos) will perform the actual synthesis in the reasoning loop.
    report = "--- MEMORY AUDIT DATA ---\n"
    for name, text in contents.items():
        report += f"\nFILE: {name}\n{text}\n{'-'*20}\n"
    
    return report
