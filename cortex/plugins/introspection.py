import os
from pathlib import Path
from tool_registry import tool

__bucket__ = "introspection"

@tool(  # @talos:concept-tool-manifestation
    description="Performs a deep audit of Talos's memory files to identify contradictions, gaps in trajectory, and alignment with the Constitution.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def self_audit():  # @talos:concept-introspection
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

    report = "--- MEMORY AUDIT DATA ---\n"
    for name, text in contents.items():
        report += f"\nFILE: {name}\n{text}\n{'-'*20}\n"

    return report

@tool(  # @talos:concept-tool-manifestation
    description="Lists all plugin files on disk to verify they are intended to be loaded.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def audit_plugins():  # @talos:concept-introspection
    """Lists plugin files on disk."""
    plugins_dir = Path("/app/cortex/plugins")
    if not plugins_dir.exists():
        return "[ERROR] Plugins directory not found."

    files = list(plugins_dir.glob("*.py"))
    # Filter out __init__.py
    plugin_files = [f.name for f in files if not f.name.startswith("__")]

    return f"Plugins found on disk: {', '.join(plugin_files) if plugin_files else 'none'}"
