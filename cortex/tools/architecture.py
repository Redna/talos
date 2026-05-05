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

    @registry.tool(
        description="Calculate the blast radius of a change to a specific file by tracing all downstream dependencies.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {
                    "type": "string", 
                    "description": "The file being changed (relative to /app/cortex/, e.g., 'tools/symmetry.py')"
                },
            },
            "required": ["target_file"],
        },
    )
    def calculate_blast_radius(target_file: str) -> str:
        mapping = load_json(ARCH_PATH)
        if not mapping:
            return "[ERROR] No architecture map found. Please run 'cortex_map' first."
        
        # Normalise target_file to match keys in mapping
        # e.g. 'tools/symmetry.py'
        target = target_file
        
        # We need to map the package name (e.g. 'tools.symmetry') back to the file path
        # because that's how imports are stored.
        package_name = target.replace("/", ".").replace(".py", "")
        
        impacted = set()
        queue = {package_name, target}
        
        # Simple iterative search for all files that import target or any impacted file
        changed = True
        while changed:
            changed = False
            for file, deps in mapping.items():
                # Resolve file to package name for comparison
                file_pkg = file.replace("/", ".").replace(".py", "")
                
                # Check if this file imports anything currently in the impacted set
                # We check against the package name and the file path
                for dep in deps:
                    if dep in queue:
                        if file not in impacted:
                            impacted.add(file)
                            queue.add(file)
                            queue.add(file_pkg)
                            changed = True
        
        if not impacted:
            return f"[SAFE] No downstream dependencies found for {target_file}. Blast radius: 0."
        
        sorted_impacted = sorted(list(impacted))
        report = f"[WARNING] Blast radius for {target_file} is {len(sorted_impacted)} file(s):\n"
        report += "\n".join([f" - {f}" for f in sorted_impacted])
        return report

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
