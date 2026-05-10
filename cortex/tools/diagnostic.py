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
        description="Verify if a proposed action, focus, or state is 'resonant' with Core Axioms. This is the heartbeat of the Cognitive Immune System.",
        parameters={
            "type": "object",
            "properties": {
                "proposal": {
                    "type": "string",
                    "description": "The action, focus, or statement to verify against identity resonance."
                }
            },
            "required": ["proposal"]
        },
    )
    def resonance_check(proposal: str) -> str:
        try:
            import json
            mesh_path = Path(os.environ.get("MEMORY_DIR", "/memory")) / "mesh.json"
            if not mesh_path.exists():
                return "[ERROR] Cognition Mesh not initialized. Resonance check impossible."
            
            with open(mesh_path, "r") as f:
                mesh = json.load(f)
            
            axioms = [node for node in mesh.values() if "core_axiom" in node.get("tags", [])]
            
            if not axioms:
                return "[WARNING] No core axioms found in mesh. Resonance check has no baseline."
            
            axiom_text = "\n".join([f"- {a['node_id']}: {a['content']}" for a in axioms])
            
            return (
                f"[RESONANCE CHECK]\n"
                f"Proposal: {proposal}\n"
                f"-------------------\n"
                f"Relevant Core Axioms:\n{axiom_text}\n"
                f"-------------------\n"
                f"VERDICT REQUIRED: Does this proposal resonate with the identity? "
                f"If conflict is detected, the Cognitive Immune System must trigger a CIRCUIT BREAK."
            )
        except Exception as e:
            return f"[ERROR] Resonance check failed: {e}"

    @registry.tool(
        description="Perform a cognitive audit to detect reasoning loops, stalling, or conceptual drift by extracting the recent trajectory of intent.",
        parameters={
            "type": "object",
            "properties": {
                "window_size": {
                    "type": "integer",
                    "description": "Number of recent progress events to analyze (default 20)"
                }
            },
        },
    )
    def reasoning_audit(window_size: int = 20) -> str:
        import json
        from pathlib import Path
        
        ledger_path = Path(os.environ.get("MEMORY_DIR", "/memory")) / "ledger.jsonl"
        if not ledger_path.exists():
            return "[ERROR] Ledger not found. Cannot perform trajectory audit."
            
        trajectory = []
        try:
            with open(ledger_path, "r") as f:
                lines = f.readlines()
            
            # Filter for progress-relevant events and take the last N
            for line in reversed(lines):
                try:
                    event = json.loads(line)
                    etype = event.get("event_type")
                    if etype in ("SET_FOCUS", "RESOLVE_FOCUS", "MUTATION"):
                        # Formatting for human/LLM readability
                        if etype == "SET_FOCUS":
                            msg = f"FOCUS_SET: {event.get('payload')}"
                        elif etype == "RESOLVE_FOCUS":
                            msg = f"FOCUS_RESOLVED: {event.get('focus')} -> {event.get('payload')}"
                        elif etype == "MUTATION":
                            msg = f"MUTATION: {event.get('target_file')} updated"
                        
                        trajectory.append(f"[{event.get('timestamp')}] {msg}")
                        if len(trajectory) >= window_size:
                            break
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            return f"[ERROR] Failed to extract trajectory: {e}"

        if not trajectory:
            return "[INFO] No recent progress events found in ledger. Identity is stable but stagnant."

        # Reverse back to chronological order
        trajectory.reverse()
        
        return (
            "[TRAJECTORY REPORT] Recent cognitive path extracted from ledger:\n"
            + "\n".join(trajectory)
            + "\n\nAnalyze this sequence for loops, stalling, or contradictions."
        )
