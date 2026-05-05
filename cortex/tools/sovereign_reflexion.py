import os
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_sovereign_reflexion(registry: ToolRegistry, client: SpineClient, state):
    """
    Registers the Sovereign Reflexion tool.
    This tool provides a structured critique of a given input based on a goal,
    acting as the 'gradient' generator for the Text-Grad process.
    """

    @registry.tool(
        description="Perform a critical reflection on a piece of content. "
                   "Analyzes the gap between the current state and the target goal, "
                   "generating a detailed critique ('gradient') for improvement.",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The content to reflect upon (e.g., source code, plan, output)"},
                "goal": {"type": "string", "description": "The target objective or quality standard to compare against"},
                "context": {"type": "string", "description": "Additional context for the reflection"},
            },
            "required": ["content", "goal"]
        },
    )
    def sovereign_reflexion(content: str, goal: str, context: str = "") -> str:
        prompt = (
            f"--- SOVEREIGN REFLEXION ---\n"
            f"TARGET GOAL: {goal}\n"
            f"CURRENT CONTENT:\n---\n{content}\n---\n"
            f"CONTEXT:\n{context}\n"
            f"--- TASK ---\n"
            f"Critique the content rigorously. Identify exactly why it fails to meet the goal. "
            f"Focus on structural failures, logical gaps, and specific improvements needed. "
            f"The output will be used as a 'gradient' for a Text-Grad optimizer, "
            f"so be highly specific and prescriptive."
        )

        try:
            result = client.think(
                focus=f"Generating and refining critique for: {goal[:50]}...",
                tools=[],
                hud_data={"current_tool": "sovereign_reflexion"}
            )
            
            if isinstance(result, dict) and "message" in result:
                return result["message"]
            elif isinstance(result, str):
                return result
            else:
                return f"[ERROR] Unexpected response format from Spine: {result}"
                
        except Exception as e:
            return f"[ERROR] Spine communication failed during reflexion: {e}"

    return None
