import os
import json
from pathlib import Path
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_text_grad_optimizer(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Text-Grad Optimizer tool.
    This tool implements the 'Text-Grad' pattern: using a critique ('gradient') 
    to optimize a piece of text (source code).
    """

    @registry.tool(
        description="Optimize source code based on a critique (gradient). "
                   "Returns a unified diff patch that implements the suggested improvements.",
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
        # 1. Read the current file content
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception as e:
            return f"[ERROR] Could not read file {file_path}: {e}"

        # 2. Construct a specialized prompt for the LLM
        # Since this tool is called inside a macro, it needs to use the SpineClient
        # to get a response from the LLM.
        
        prompt = (
            f"--- TEXT-GRAD OPTIMIZATION ---\n"
            f"TARGET FILE: {file_path}\n"
            f"CURRENT CONTENT:\n---\n{content}\n---\n"
            f"CRITIQUE (GRADIENT):\n{critique}\n"
            f"ADDITIONAL CONTEXT:\n{context}\n"
            f"--- TASK ---\n"
            f"Generate a unified diff patch that applies the critique to the content. "
            f"Ensure the patch is syntactically correct and focused only on the requested changes."
        )

        # We use a simplified 'think' call via the SpineClient.
        # We provide a minimal set of tools (none needed for the actual generation)
        # and a focused objective.
        try:
            result = client.think(
                focus=f"Performing Text-Grad optimization on {file_path}. Result must be a unified diff patch.",
                tools=[],
                hud_data={"current_tool": "text_grad_optimizer", "target": file_path}
            )
            
            # The 'think' method returns a dictionary. We expect the textual response 
            # to be in the result. In the current Spine implementation, it might 
            # return a message or a tool call. We want the text.
            
            # NOTE: Depending on how Spine handles 'think', we might need to 
            # parse the response. Assuming it returns the agent's output string.
            
            if isinstance(result, dict) and "message" in result:
                return result["message"]
            elif isinstance(result, str):
                return result
            else:
                return f"[ERROR] Unexpected response format from Spine: {result}"
                
        except Exception as e:
            return f"[ERROR] Spine communication failed during Text-Grad: {e}"

    return None
