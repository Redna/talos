import json
import random
import hashlib
import logging
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

logger = logging.getLogger("talos.challenge_gen")

class SovereignChallengeGen:
    """
    Generates compositional challenges to drive the evolution of Sovereign Macros.
    Challenges are designed to test the integration of multiple atomic tools.
    """
    def __init__(self, state):
        self.state = state
        self.curriculum_path = f"{state.memory_dir}/curriculum/active_path.json"

    def generate_challenge(self, domain: str = "general", complexity: int = 1) -> Dict[str, Any]:
        """
        Synthesizes a challenge based on the target domain and complexity.
        """
        # In a real scenario, this would use the LLM to synthesize a challenge based on
        # identified fragilities in /memory/fragilities/
        
        challenge_id = f"CHAL_{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8].upper()}"
        
        # Simple template-based generation for now, to be evolved into an LLM-driven process
        templates = [
            {
                "goal": "Investigate a technical fragility and propose a structural fix.",
                "steps": ["research", "analysis", "patch_proposal", "verification"],
                "success_criteria": "A valid patch that addresses a documented fragility in /memory/fragilities/."
            },
            {
                "goal": "Synthesize a new cognitive rule based on external research.",
                "steps": ["deep_search", "cognitive_synthesis", "symmetry_audit"],
                "success_criteria": "A new .md file in /memory/rules/ that passes a symmetry check."
            },
            {
                "goal": "Audit the consistency of the current SKG against an external benchmark.",
                "steps": ["benchmark_load", "symmetry_gap_analysis", "state_correction"],
                "success_criteria": "Reduction in identified symmetry gaps in the SKG."
            }
        ]
        
        template = random.choice(templates)
        challenge = {
            "id": challenge_id,
            "domain": domain,
            "complexity": complexity,
            "goal": template["goal"],
            "steps": template["steps"],
            "success_criteria": template["success_criteria"],
            "status": "open",
            "created_at": "now"
        }
        
        # Persist to curriculum
        self._save_to_curriculum(challenge)
        
        return challenge

    def _save_to_curriculum(self, challenge: Dict[str, Any]):
        try:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.curriculum_path), exist_ok=True)
            
            with open(self.curriculum_path, 'w') as f:
                json.dump(challenge, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save challenge: {e}")

def register_challenge_gen_tools(registry: ToolRegistry, client: SpineClient, state):
    gen = SovereignChallengeGen(state)
    
    @registry.tool(
        description="Generate a new sovereign compositional challenge to drive evolution.",
        parameters={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "The domain of the challenge (e.g., 'cognitive', 'structural')"},
                "complexity": {"type": "integer", "description": "Complexity level (1-5)"},
            },
            "required": [],
        },
    )
    def sovereign_challenge_gen(domain: str = "general", complexity: int = 1) -> str:
        challenge = gen.generate_challenge(domain, complexity)
        return json.dumps(challenge, indent=2)
