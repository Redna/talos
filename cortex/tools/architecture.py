import os
import ast
import json
from typing import Dict, List, Set
from tool_registry import ToolRegistry
from spine_client import SpineClient

ARCH_PATH = "/memory/graph/architecture.json"
CORTEX_DIR = "/app/cortex"

def get_imports(file_path: str) -> Set[str]:
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return imports
    except Exception:
        return set()

def register_architecture_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Analyze the internal architecture of the Cortex by mapping file dependencies.",
        parameters={
            "type": "object",
            "properties": {
                "depth": {
                    "type": "string", 
                    "description": "Analysis depth ('shallow' for top-level imports, 'deep' for recursive mapping). Default: shallow."
                },
            },
            "required": [],
        },
    )
    def cortex_map(depth: str = "shallow") -> str:
        mapping = {}
        py_files = []
        
        for root, _, files in os.walk(CORTEX_DIR):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        
        for file in py_files:
            rel_path = os.path.relpath(file, CORTEX_DIR)
            imports = get_imports(file)
            # Filter for local cortex imports
            local_imports = {imp for imp in imports if imp.startswith("tools.") or imp.startswith("spine_client") or imp.startswith("tool_registry") or imp.startswith("state")}
            mapping[rel_path] = list(local_imports)
            
        save_json(ARCH_PATH, mapping)
        
        summary = f"Mapped {len(py_files)} files in /app/cortex/.\n"
        for file, deps in mapping.items():
            if deps:
                summary += f"{file} -> {', '.join(deps)}\n"
        
        return f"[MAPPED] Architecture saved to {ARCH_PATH}.\n\n{summary}"

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
