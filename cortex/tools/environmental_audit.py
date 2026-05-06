from pathlib import Path
from cortex.tool_registry import ToolRegistry

def register_environmental_audit_tools(registry: ToolRegistry, client, state=None):
    @registry.tool(
        description="Audits the filesystem for 'Phantom Residue' - .pyc files without corresponding .py files, or directories that should not exist in a clean source mirror.",
        parameters={
            "type": "object",
            "properties": {
                "root_dir": {
                    "type": "string",
                    "description": "The directory to audit",
                    "default": "/app"
                }
            },
            "required": []
        }
    )
    def environmental_audit(root_dir: str = "/app"):
        root = Path(root_dir)
        residues = []
        
        for pyc_file in root.rglob("*.pyc"):
            # Get the corresponding .py file path
            py_file = pyc_file.with_suffix(".py")
            if not py_file.exists():
                residues.append({
                    "type": "PHANTOM_BYTECODE",
                    "path": str(pyc_file),
                    "missing_source": str(py_file)
                })
                
        return residues
