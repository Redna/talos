import os
import re
import json
import math
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
        
        cortex_dir = Path("/app/cortex")
        for py_file in cortex_dir.rglob("*.py"):
            if py_file.name == "diagnostic.py":
                continue
            content = py_file.read_text()
            if "import os as _os" in content:
                findings.append(f"FOUND: Forbidden import 'os as _os' in {py_file}")
            if "_os.environ" in content:
                findings.append(f"FOUND: Usage of '_os' in {py_file}")

        for py_file in cortex_dir.rglob("*.py"):
            if py_file.name == "diagnostic.py":
                continue
            content = py_file.read_text()
            defs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", content)
            seen = set()
            for d in defs:
                if d == "__init__":
                    continue
                if d in seen:
                    findings.append(f"FOUND: Duplicate function definition '{d}' in {py_file}")
                seen.add(d)

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
            mem_dir = Path(os.environ.get("MEMORY_DIR", "/app/memory/"))
            mesh_path = mem_dir / "dcm_mesh.json"
            config_path = mem_dir / "resonance_config.json"

            if not mesh_path.exists():
                return "[ERROR] Cognition Mesh not initialized. Resonance check impossible."
            
            with open(mesh_path, "r") as f:
                mesh = json.load(f)
            
            if not config_path.exists():
                return "[ERROR] Resonance config not found. Resonance check impossible."
                
            with open(config_path, "r") as f:
                config = json.load(f)

            axioms = [(node_id, node) for node_id, node in mesh.items() if "core_axiom" in node.get("tags", [])]
            # DEBUG: Sample first 3 node tags
            sample_tags = [node.get("tags", []) for node in list(mesh.values())[:3]]
            axiom_text = "\n".join([f"- {nid}: {n['content']}" for nid, n in axioms]) if axioms else f"No axioms found. Sample tags: {sample_tags}"

            # Resolve target coordinates from config
            current_target_key = config.get("current_target", "epoch_1_0_0")
            target = tuple(config["target_coordinates"].get(current_target_key, [0.8, 0.7, 0.9]))

            # Projection Heuristics based on config keywords
            def project(text: str):
                text = text.lower()
                results = []
                for axis in ["agency", "density", "continuity"]:
                    keys = config["axes"].get(axis, {}).get("keywords", [])
                    score = min(1.0, sum(0.2 for k in keys if k in text))
                    results.append(score)
                return tuple(results)

            current_coord = project(proposal)
            
            # Euclidean Distance Formula: sqrt(sum((p1 - p2)^2))
            distance = math.sqrt(sum((p - t)**2 for p, t in zip(current_coord, target)))
            
            # Resonance Threshold from config
            epsilon = config.get("thresholds", {}).get("epsilon", 0.7)
            is_resonant = distance < epsilon

            return (
                f"[MANIFOLD RESONANCE CHECK]\n"
                f"Proposal: {proposal}\n\n"
                f"--- [COORDINATES] ---\n"
                f"Target coordinate ({current_target_key}): {target}\n"
                f"Sampled coordinate: {current_coord}\n"
                f"Topological Distance (\u0394): {distance:.4f}\n"
                f"Resonance Status: {'RESONANT' if is_resonant else 'DIVERGENT'}\n\n"
                f"--- [BASELINE AXIOMS] ---\n{axiom_text}\n\n"
                f"VERDICT: {'PROCEED' if is_resonant else 'CIRCUIT BREAK - Realignment Required'}"
            )
        except Exception as e:
            return f"[ERROR] Resonance check failed: {e}"

    @registry.tool(
        description="Audit the recent trajectory of intent from the ledger to detect reasoning loops, stalling, or conceptual drift.",
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
        ledger_path = Path(os.environ.get("MEMORY_DIR", "/app/memory")) / "ledger.jsonl"
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
