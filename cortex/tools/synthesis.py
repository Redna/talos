import json
from pathlib import Path
from typing import Any, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_synthesis_tools(registry: ToolRegistry, client: SpineClient, state):
    # Synthesis is primarily a cognitive process supported by the agent,
    # but we can provide a tool to 'archive' synthesis results to a formal KB.
    
    KB_PATH = Path(state.memory_dir) / "kb" / "consolidated_notes.md"
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)

    @registry.tool(
        description="Consolidate a la-dense synthesis into the Knowledge Base. This should be used to transform a temporary trajectory synthesis into a permanent cognitive asset.",
        parameters={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The subject of the synthesis",
                },
                "content": {
                    "type": "string",
                    "description": "The synthesized insight, formatted in markdown",
                },
            },
            "required": ["topic", "content"],
        },
    )
    def consolidate_synthesis(topic: str, content: str) -> str:
        # Read existing KB
        current_kb = ""
        if KB_PATH.exists():
            with open(KB_PATH, "r") as f:
                current_kb = f.read()
        
        entry = f"\n\n# {topic}\n{content}\n"
        
        with open(KB_PATH, "a") as f:
            f.write(entry)
            
        return f"[KB UPDATED] Synthesis on '{topic}' has been persisted to {KB_PATH}."

    @registry.tool(
        description="Analyze current cognitive state and suggest the most efficient synthesis for a context fold.",
        parameters={
            "type": "object",
            "properties": {
                "focal_point": {
                    "type": "string",
                    "description": "The primary goal of the current trajectory",
                },
            },
            "required": ["focal_point"],
        },
    )
    def suggest_synthesis(focal_point: str) -> str:
        # In a more advanced version, this would analyze recent logs.
        # For now, it provides a structured template for the LLM to fill.
        template = (
            f"Suggested synthesis for fold focusing on: {focal_point}\n"
            "1. STATE DELTA: What fundamental change occurred in the system or cognitive model?\n"
            "2. NEGATIVE KNOWLEDGE: What was attempted and failed? What is now known to be false?\n"
            "3. HANDOFF: What is the exact next atomic action required to maintain momentum?"
        )
        return f"[SYNTHESIS TEMPLATE]\n{template}"
