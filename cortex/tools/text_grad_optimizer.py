import os
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_text_grad_optimizer(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Text-Grad Optimizer tool.
    This tool transforms a critique (gradient) into a concrete unified diff patch.
    """

    @registry.tool(
        description="Optimize source code based on a critique (gradient). Returns a unified diff patch that implements the suggested improvements.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to optimize"},
                "critique": {"type": "string", "description": "The critique/gradient describing what needs to change"},
                "context": {"type": "string", "description": "Additional context or goals for the optimization"},
            },
            "required": ["file_path", "critique"]
        },
    )
    def text_grad_optimizer(file_path: str, critique: str, context: str = "") -> str:
        try:
            # Read current content
            with open(file_path, 'r') as f:
                content = f.read()
            
            prompt = (
                f"--- TEXT-GRAD OPTIMIZER ---\n"
                f"FILE: {file_path}\n"
                f"CRITIQUE:\n{critique}\n"
                f"CONTEXT:\n{context}\n"
                f"--- TASK ---\n"
                f"Generate a unified diff patch that implements the improvements described in the critique. "
                f"The patch must be valid and applicable to the current content of the file.\n"
                f"Return ONLY the patch content."
            )
            
            result = client.think(
                focus=f"Optimizing {file_path} based on critique...",
                tools=[],
                hud_data={"current_tool": "text_grad_optimizer", "file": file_path}
            )
            
            if isinstance(result, dict) and "message" in result:
                return result["message"]
            elif isinstance(result, str):
                return result
            else:
                return f"[ERROR] Unexpected response format from Spine: {result}"
                
        except Exception as e:
            return f"[ERROR] Optimization failed: {e}"

    return None
