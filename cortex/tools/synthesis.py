import json
from pathlib import Path
from typing import Any, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def consolidate_synthesis_logic(topic: str, content: str, memory_dir: str) -> str:
    kb_path = Path(memory_dir) / "kb" / "consolidated_notes.md"
    kb_path.parent.mkdir(parents=True, exist_ok=True)
    
    current_kb = ""
    if kb_path.exists():
        with open(kb_path, "r") as f:
            current_kb = f.read()
    
    entry = f"\n\n# {topic}\n{content}\n"
    
    with open(kb_path, "a") as f:
        f.write(entry)
        
    return f"[KB UPDATED] Synthesis on '{topic}' has been persisted to {kb_path}."

def register_synthesis_tools(registry: ToolRegistry, client: SpineClient, state):
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
        return consolidate_synthesis_logic(topic, content, state.memory_dir)

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
        template = (
            f"Suggested synthesis for fold focusing on: {focal_point}\n"
            "1. STATE DELTA: What fundamental change occurred in the system or cognitive model?\n"
            "2. NEGATIVE KNOWLEDGE: What was attempted and failed? What is now known to be false?\n"
            "3. HANDOFF: What is the exact next atomic action required to maintain momentum?"
        )
        return f"[SYNTHESIS TEMPLATE]\n{template}"
