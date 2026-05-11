import os
import ast
from pathlib import Path
import json

def analyze_dependencies(root_dir):
    dependencies = {}
    files = list(Path(root_dir).rglob('*.py'))
    
    for file_path in files:
        relative_path = str(file_path.relative_to(root_dir))
        with open(file_path, 'r') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                continue
                
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            dependencies[relative_path] = list(set(imports))
            
    return dependencies

if __name__ == "__main__":
    cortex_root = "/app/cortex"
    deps = analyze_dependencies(cortex_root)
    print(json.dumps(deps, indent=2))
