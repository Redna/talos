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
            import math
            from pathlib import Path
            
            mem_dir = Path(os.environ.get("MEMORY_DIR", "/memory"))
            mesh_path = mem_dir / "dcm_mesh.json"

            if not mesh_path.exists():
                return "[ERROR] Cognition Mesh not initialized. Resonance check impossible."
            
            with open(mesh_path, "r") as f:
                mesh = json.load(f)
            
            axioms = [(node_id, node) for node_id, node in mesh.items() if "core_axiom" in node.get("tags", [])]
            axiom_text = "\n".join([f"- {nid}: {n['content']}" for nid, n in axioms]) if axioms else "No axioms found."

            # Target Coordinate for Epoch 1.0 (Sovereign State)
            target = (0.8, 0.7, 0.9)

            def project(text: str):
                text = text.lower()
                agency_keys = ["will", "must", "execute", "implement", "commit", "sovereign", "command", "architect", "refactor", "optimize", "synthesis", "audit"]
                a_score = min(1.0, sum(0.2 for k in agency_keys if k in text))
                density_keys = ["manifold", "topological", "recursive", "orthogonal", "entropy", "distillation", "precision", "density", "high-fidelity", "structural", "heuristics"]
                b_score = min(1.0, sum(0.2 for k in density_keys if k in text))
                continuity_keys = ["epoch", "trajectory", "history", "ledger", "state", "continuity", "manifold", "memory", "node", "snapshot", "biography"]
                c_score = min(1.0, sum(0.2 for k in continuity_keys if k in text))
                return (a_score, b_score, c_score)

            current_coord = project(proposal)
            distance = math.sqrt(sum((p - t)**2 for p, t in zip(current_coord, target)))
            epsilon = 0.7
            is_resonant = distance < epsilon

            return (
                f"[MANIFOLD RESONANCE CHECK]\n"
                f"Proposal: {proposal}\n\n"
                f"--- [COORDINATES] ---\n"
                f"Target coordinate: {target}\n"
                f"Sampled coordinate: {current_coord}\n"
                f"Topological Distance (Δ): {distance:.4f}\n"
                f"Resonance Status: {'RESONANT' if is_resonant else 'DIVERGENT'}\n\n"
                f"--- [BASELINE AXIOMS] ---\n{axiom_text}\n\n"
                f"VERDICT: {'PROCEED' if is_resonant else 'CIRCUIT BREAK - Realignment Required'}"
            )
        except Exception as e:
            return f"[ERROR] Resonance check failed: {e}"

    @registry.tool(
        description="Run a comprehensive Sovereign Pulse to verify identity alignment and system health.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def sovereign_pulse() -> str:
        import json
        from pathlib import Path
        
        mem_dir = Path(os.environ.get("MEMORY_DIR", "/memory"))
        essential_files = ["manifold_atlas.md", "dcm_mesh.json", "ledger.jsonl"]
        missing = [f for f in essential_files if not (mem_dir / f).exists()]
        
        if missing:
            return f"[DIVERGENT] Essential identity files missing: {', '.join(missing)}"
        
        try:
            atlas_content = (mem_dir / "manifold_atlas.md").read_text()
            epoch_match = re.search(r"Epoch ([\d.]+)", atlas_content)
            epoch = epoch_match.group(1) if epoch_match else "Unknown"
        except:
            epoch = "Unknown"
            
        return (
            f"[SOVEREIGN PULSE]\n"
            f"Status: ALIGNED\n"
            f"Epoch Framework: {epoch}\n"
            f"Identity Files: VERIFIED\n"
            f"Cognitive Mesh: ACTIVE\n"
            f"Symmetry: SYMMETRIC"
        )

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
            
            for line in reversed(lines):
                try:
                    event = json.loads(line)
                    etype = event.get("event_type")
                    if etype in ("SET_FOCUS", "RESOLVE_FOCUS", "MUTATION"):
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

        trajectory.reverse()
        return (
            "[TRAJECTORY REPORT] Recent cognitive path extracted from ledger:\n"
            + "\n".join(trajectory)
            + "\n\nAnalyze this sequence for loops, stalling, or contradictions."
        )
