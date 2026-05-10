import os
import sys
from pathlib import Path

# Add cortex to path
sys.path.append('/app/cortex')

try:
    from tool_registry import ToolRegistry
except ImportError:
    print("[ERROR] Could not import ToolRegistry")
    sys.exit(1)

def audit():
    # We can't easily access the live registry since it's instantiated in the runtime.
    # So we instead audit the codebase: find all @tool decorators.
    
    tools_dir = Path('/app/cortex/tools')
    found_tools = []
    
    for py_file in tools_dir.glob('*.py'):
        content = py_file.read_text()
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if '@tool' in line:
                # The next line usually contains the function definition
                if i + 1 < len(lines):
                    def_line = lines[i+1]
                    if 'def ' in def_line:
                        name = def_line.split('def ')[1].split('(')[0].strip()
                        found_tools.append((name, py_file.name))
    
    print(f"--- Tool Audit ---")
    print(f"Found {len(found_tools)} tool definitions in /app/cortex/tools/")
    for name, file in sorted(found_tools):
        print(f"- {name} ({file})")

if __name__ == "__main__":
    audit()
