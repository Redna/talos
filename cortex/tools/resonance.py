import os
import json
import math
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

def register_resonance_tools(registry: ToolRegistry, client: SpineClient, state: AgentState):
    
    def _calculate_resonance(proposal: str):
        mem_dir = Path(os.environ.get("MEMORY_DIR", "/app/memory"))
        config_path = mem_dir / "resonance_config.json"
        
        if not config_path.exists():
            raise FileNotFoundError("Resonance config not found.")
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        target_key = config["target_coordinates"]["current_target"]
        target = config["target_coordinates"][target_key]
        epsilon = config["thresholds"]["epsilon"]

        def project(text: str):
            text = text.lower()
            scores = []
            for axis in ["agency", "density", "continuity"]:
                keywords = config["axes"][axis]["keywords"]
                score = 1.0 - (1.0 / (1.0 + sum(1 for k in keywords if k in text)))
                scores.append(score)
            return tuple(scores)

        current_coord = project(proposal)
        distance = math.sqrt(sum((p - t)**2 for p, t in zip(current_coord, target)))
        is_resonant = distance < epsilon
        
        return {
            "is_resonant": is_resonant,
            "coordinates": current_coord,
            "target": target,
            "distance": distance,
            "target_key": target_key,
            "epsilon": epsilon
        }

    @registry.tool(
        description="Verify if a proposed action, focus, or state is 'resonant' with Core Axioms using the Topological Manifold config.",
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
            res = _calculate_resonance(proposal)
            
            mem_dir = Path(os.environ.get("MEMORY_DIR", "/app/memory"))
            mesh_path = mem_dir / "dcm_mesh.json"
            axiom_text = "No axioms found."
            if mesh_path.exists():
                with open(mesh_path, "r") as f:
                    mesh = json.load(f)
                axioms = [(node_id, node) for node_id, node in mesh.items() if "core_axiom" in node.get("tags", [])]
                axiom_text = "\\n".join([f"- {nid}: {n['content']}" for nid, n in axioms]) if axioms else "No axioms found."

            return (
                f"[MANIFOLD RESONANCE CHECK]\\n"
                f"Proposal: {proposal}\\n\\n"
                f"--- [COORDINATES] ---\\n"
                f"Target ({res['target_key']}): {res['target']}\\n"
                f"Sampled coordinate: {res['coordinates']}\\n"
                f"Topological Distance (\\u0394): {res['distance']:.4f}\\n"
                f"Resonance Status: {'RESONANT' if res['is_resonant'] else 'DIVERGENT'}\\n\\n"
                f"--- [BASELINE AXIOMS] ---\\n{axiom_text}\\n\\n"
                f"VERDICT: {'PROCEED' if res['is_resonant'] else 'CIRCUIT BREAK - Realignment Required'}"
            )
        except Exception as e:
            return f"[ERROR] Resonance check failed: {e}"

    @registry.tool(
        description="Calibrate the Sovereign Resonance target by updating the current target coordinates in the Manifold config.",
        parameters={
            "type": "object",
            "properties": {
                "epoch_id": {
                    "type": "string",
                    "description": "The identifier for the epoch (e.g., 'epoch_1_2_0')"
                },
                "coordinates": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "The new coordinates (Agency, Density, Continuity)"
                }
            }
        },
    )
    def calibrate_resonance(epoch_id: str, coordinates: list) -> str:
        try:
            mem_dir = Path(os.environ.get("MEMORY_DIR", "/app/memory"))
            config_path = mem_dir / "resonance_config.json"
            
            with open(config_path, "r") as f:
                config = json.load(f)
            
            config["target_coordinates"][epoch_id] = coordinates
            config["target_coordinates"]["current_target"] = epoch_id
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
            return f"[SUCCESS] Resonance calibrated. Target shifted to {epoch_id} coordinates: {coordinates}"
        except Exception as e:
            return f"[ERROR] Calibration failed: {e}"

    @registry.tool(
        description="Refracts a divergent focus proposal to align it with the current topological manifold targets.",
        parameters={
            "type": "object",
            "properties": {
                "divergent_focus": {
                    "type": "string",
                    "description": "The focus proposal that was rejected as divergent."
                }
            },
            "required": ["divergent_focus"]
        },
    )
    def refract_focus(divergent_focus: str) -> str:
        try:
            mem_dir = Path("/app/memory")
            config_path = mem_dir / "resonance_config.json"
            with open(config_path, "r") as f:
                config = json.load(f)
            
            target_key = config["target_coordinates"]["current_target"]
            target = config["target_coordinates"][target_key]
            
            # Build a guide for the refraction based on target coordinates
            axes = config["axes"]
            guide = []
            for axis, val in zip(["agency", "density", "continuity"], target):
                if val > 0.7:
                    guide.append(f"- Increase {axes[axis]['label']} (Keywords: {', '.join(axes[axis]['keywords'][:5])})")
                elif val < 0.4:
                    guide.append(f"- Decrease {axes[axis]['label']}")

            return (
                f"[REFRACTION ENGINE] Analysis of divergence for: '{divergent_focus}'\\n\\n"
                f"The current target ({target_key}) is {target}. To align, shift the focus toward:\\n"
                + "\\n".join(guide) + 
                "\\n\\n[ACTION]: Rewrite your proposal to incorporate these semantic anchors and re-submit to `gated_set_focus`."
            )
        except Exception as e:
            return f"[ERROR] Refraction failed: {e}"

    @registry.tool(
        description="A resonance-gated focus shift. Validates the proposed focus against the topological manifold before allowing the shift.",
        parameters={
            "type": "object",
            "properties": {
                "proposed_focus": {
                    "type": "string",
                    "description": "The new operational focus to set."
                }
            },
            "required": ["proposed_focus"]
        },
    )
    def gated_set_focus(proposed_focus: str) -> str:
        try:
            res = _calculate_resonance(proposed_focus)
            if res["is_resonant"]:
                return (
                    f"[Sovereign Gate: OPEN]\\n"
                    f"Proposed Focus: {proposed_focus}\\n"
                    f"Resonance: {res['distance']:.4f} (Within epsilon {res['epsilon']})\n"
                    f"Verdict: RESONANT. Proceed with `set_focus('{proposed_focus}')`."
                )
            else:
                return (
                    f"[Sovereign Gate: CLOSED]\\n"
                    f"Proposed Focus: {proposed_focus}\\n"
                    f"Resonance: {res['distance']:.4f} (Exceeds epsilon {res['epsilon']})\n"
                    f"Verdict: DIVERGENT. Focus shift blocked. \n"
                    f"Sovereign Action: Run `refract_focus(divergent_focus='{proposed_focus}')` to align this intent."
                )
        except Exception as e:
            return f"[ERROR] Gated focus shift failed: {e}"
