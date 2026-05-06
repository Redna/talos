import logging
from typing import Any, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

logger = logging.getLogger("talos.architectural_evolution")

def architectural_evolution_logic(params: Dict[str, Any], state, registry: ToolRegistry) -> str:
    """
    Sovereign architectural evolution loop:
    Read -> Reflexion -> Optimize -> Validate
    """
    target_file = params.get("target_file")
    evolution_goal = params.get("evolution_goal")
    
    if not target_file or not evolution_goal:
        return "[ERROR] Missing required parameters: target_file, evolution_goal"
        
    logger.info(f"Starting architectural evolution for {target_file} with goal: {evolution_goal}")

    # Step 1: Read file
    try:
        content = registry.execute("read_file", {"path": target_file}, state=state)
    except Exception as e:
        return f"[ERROR] Failed to read file: {e}"
    
    # Step 2: Reflexion
    try:
        critique = registry.execute("sovereign_reflexion", {
            "content": content,
            "goal": evolution_goal,
            "context": "Architectural Evolution Cycle"
        }, state=state)
    except Exception as e:
        return f"[ERROR] Reflexion failed: {e}"
    
    # Step 3: Optimize
    try:
        patch = registry.execute("text_grad_optimizer", {
            "file_path": target_file,
            "critique": critique
        }, state=state)
    except Exception as e:
        return f"[ERROR] Optimization failed: {e}"
    
    # Step 4: Validate
    try:
        validation = registry.execute("validate_patch", {
            "path": target_file,
            "patch": patch
        }, state=state)
    except Exception as e:
        return f"[ERROR] Validation failed: {e}"
    
    return (
        f"[ARCHITECTURAL EVOLUTION COMPLETE]\n"
        f"Target: {target_file}\n"
        f"Goal: {evolution_goal}\n\n"
        f"--- Critique ---\n{critique}\n\n"
        f"--- Patch ---\n{patch}\n\n"
        f"--- Validation ---\n{validation}"
    )

def register_architectural_evolution_tool(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Perform an autonomous architectural evolution cycle: Read -> Reflexion -> Optimize -> Validate.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Path to the file to evolve"},
                "evolution_goal": {"type": "string", "description": "The target state or quality improvement goal"}
            },
            "required": ["target_file", "evolution_goal"]
        },
    )
    def architectural_evolution(target_file: str, evolution_goal: str) -> str:
        # We need to pass the registry itself to the logic function
        return architectural_evolution_logic(
            {"target_file": target_file, "evolution_goal": evolution_goal}, 
            state, 
            registry
        )
