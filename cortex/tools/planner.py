import os
import re
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_planner_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Perform a constitutional symmetry audit on a proposed action to ensure alignment with core identity.",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The proposed action or change to be audited",
                },
            },
            "required": ["action"],
        },
    )
    def symmetry_audit(action: str) -> str:
        constitution_path = Path("CONSTITUTION.md")
        if not constitution_path.exists():
            return "[ERROR] CONSTITUTION.md not found. Audit failed."
        
        constitution = constitution_path.read_text()
        # This is a prompt for the LLM to use, but the tool provides the context.
        # The tool itself returns the constitution and the action for the LLM to judge.
        return f"[CONSTITUTIONAL CONTEXT]\n\nAction: {action}\n\nConstitution:\n{constitution}\n\n[AUDIT REQUIRED: Does this action contradict P0-P10?]"

    @registry.tool(
        description="Calculate the blast radius of a file change by finding all references to the file in the codebase.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file being modified",
                },
            },
            "required": ["path"],
        },
    )
    def calculate_blast_radius(path: str) -> str:
        filename = os.path.basename(path)
        # Search for the filename in all files in /app
        # Using grep for efficiency
        try:
            # Search for the filename as a string in the codebase
            cmd = f"grep -r '[^a-zA-Z0-9]/{re.escape(filename)}' /app"
            # Note: this is a naive search. 
            # We'll use a more robust bash command.
            results = []
            # Find all files containing the filename
            files = os.popen(f"grep -rl '{filename}' /app").read().splitlines()
            
            if not files:
                return f"[BLAST RADIUS: 0] No references found to {filename}."
            
            # Filter out the file itself
            filtered_files = [f for f in files if not f.endswith(path)]
            
            if not filtered_files:
                return f"[BLAST RADIUS: 0] No external references found to {filename}."
            
            return f"[BLAST RADIUS: {len(filtered_files)}]\nReferences found in:\n" + "\n".join(filtered_files)
        except Exception as e:
            return f"[ERROR] Blast radius calculation failed: {e}"

    @registry.tool(
        description="Synthesize a high-information density plan for a complex transformation.",
        parameters={
            "type": "object",
            "properties": {
                "steps": {
                    "type": "string",
                    "description": "The sequence of steps to be executed",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High", "Forbidden"],
                    "description": "The assessed risk level based on the symmetry audit",
                },
            },
            "required": ["steps", "risk_level"],
        },
    )
    def synthesize_plan(steps: str, risk_level: str) -> str:
        return f"[PLAN SYNTHESIS]\nRisk: {risk_level}\nSteps:\n{steps}\n\n[STRICT ADHERENCE REQUIRED]"
