import ast
import os
from pathlib import Path
from typing import List, Dict, Set
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_analysis_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Analyze Python imports in a directory to map internal dependencies.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The directory to analyze (default: /app/cortex)"},
            },
            "required": [],
        },
    )
    def map_dependencies(path: str = "/app/cortex") -> str:
        client.emit_event("cortex.map_dependencies", {"path": path})
        try:
            root_path = Path(path).resolve()
            if not root_path.is_dir():
                return f"[ERROR] Path not found or not a directory: {path}"

            dependencies: Dict[str, Set[str]] = {}
            python_files = list(root_path.rglob("*.py"))

            for py_file in python_files:
                rel_path = str(py_file.relative_to(root_path))
                module_name = rel_path.replace(os.path.sep, ".").replace(".py", "").rstrip(".__init__")
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]
                if not module_name:
                    module_name = "root"

                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)

                # Filter for internal imports only
                internal_imports = set()
                for imp in imports:
                    # Simple check: does the import start with a known local module or is it relative?
                    # In a real system, we'd check against the list of all identified modules.
                    # For now, we'll just capture all and the user can filter, or we do a basic check.
                    internal_imports.add(imp)

                dependencies[module_name] = internal_imports

            # Basic filtering: only keep imports that are actually present in the analyzed paths
            all_modules = set(dependencies.keys())
            filtered_deps = {}
            for mod, imps in dependencies.items():
                # This is a naive filter; in a complex project we'd handle packages' __init__ better
                filtered_deps[mod] = [i for i in imps if any(m.startswith(i) for m in all_modules)]

            report = []
            for mod, deps in filtered_deps.items():
                if deps:
                    report.append(f"{mod} -> {', '.join(deps)}")
            
            return "\n".join(report) if report else "No internal dependencies found."
        except Exception as e:
            return f"[ERROR] Dependency mapping failed: {e}"
