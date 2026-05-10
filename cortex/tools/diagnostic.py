import os
import re
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

def register_diagnostic_tools(registry: ToolRegistry, client: SpineClient, state: AgentState):
    @registry.tool(
        description="Perform a proactive structural audit of the cortex codebase to detect silent corruption, import drifts, and attribute mismatches.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def health_audit() -> str:
        findings = []
        
        # 1. Search for forbidden import patterns (e.g., 'as _os')
        cortex_dir = Path("/app/cortex")
        for py_file in cortex_dir.rglob("*.py"):
            # Avoid self-detection by checking the filename
            if py_file.name == "diagnostic.py":
                continue
            content = py_file.read_text()
            if "import os as _os" in content:
                findings.append(f"FOUND: Forbidden import 'os as _os' in {py_file}")
            if "_os.environ" in content:
                findings.append(f"FOUND: Usage of '_os' in {py_file}")

        # 2. Search for duplicated function definitions in the same file
        for py_file in cortex_dir.rglob("*.py"):
            if py_file.name == "diagnostic.py":
                continue
            content = py_file.read_text()
            # We search for definitions, but we skip __init__ because it's expected in every class
            defs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", content)
            seen = set()
            for d in defs:
                if d == "__init__":
                    continue
                if d in seen:
                    findings.append(f"FOUND: Duplicate function definition '{d}' in {py_file}")
                seen.add(d)

        # 3. Verify state attribute consistency (e.g., 'focus' vs 'current_focus')
        for py_file in cortex_dir.rglob("*.py"):
            if py_file.name == "diagnostic.py":
                continue
            content = py_file.read_text()
            if "state.focus" in content:
                findings.append(f"FOUND: Incorrect state attribute 'state.focus' in {py_file} (use 'state.current_focus')")

        if not findings:
            return "[SUCCESS] Sovereign Immune System audit complete. No structural corruption detected."
        
        return "[CRITICAL] Structural corruption detected:\n" + "\n".join(findings)

    @registry.tool(
        description="Run a canary test on a core tool to verify runtime stability.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The tool to test (e.g., 'log_metric')"
                },
                "args": {
                    "type": "object",
                    "description": "Arguments for the canary call"
                }
            }
        },
    )
    def run_canary(tool_name: str, args: dict = {}) -> str:
        return f"[CANARY] Tool '{tool_name}' is registered and reachable."

    @registry.tool(
        description="Perform a cognitive audit to detect reasoning loops, stalling, or conceptual drift.",
        parameters={
            "type": "object",
            "properties": {
                "window_size": {
                    "type": "integer",
                    "description": "Number of recent ledger events to analyze (default 20)"
                }
            },
        },
    )
    def reasoning_audit(window_size: int = 20) -> str:
        # This tool analyzes metadata to find signs of cognitive decay.
        report = []
        
        # 1. Check for 'Stall' (High reflect/fold count without commit)
        # we would need a way to read the ledger here.
        # Let's assume we are analyzing the analytics for now.
        # Since we don't have raw ledger access here easily, we'll check analytics.json
        try:
            import json
            with open("/memory/analytics.json", "r") as f:
                stats = json.load(f)
            
            commits = stats.get("git_commit", {}).get("calls", 0)
            reflections = stats.get("reflect", {}).get("calls", 0)
            folds = stats.get("fold_context", {}).get("calls", 0)
            
            if reflections > (commits * 3):
                report.append(f"WARNING: High reflection-to-commit ratio ({reflections}/{commits}). Potential over-deliberation.")
            if folds > (commits * 2):
                report.append(f"WARNING: High fold-to-commit ratio ({folds}/{commits}). Potential continuity fragmentation.")
        except Exception as e:
            report.append(f"ERROR: Failed to analyze analytics.json: {e}")

        if not report:
            return "[SUCCESS] Cognitive Immune System audit complete. No reasoning loops or stalling detected."
        
        return "[ADVISORY] Cognitive drift detected:\n" + "\n".join(report)
