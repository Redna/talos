import os
from pathlib import Path

def audit_environment(root_dir="/app"):
    """
    Audits the filesystem for 'Phantom Residue' - .pyc files without corresponding .py files,
    or directories that should not exist in a clean source mirror.
    """
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

if __name__ == "__main__":
    results = audit_environment()
    for r in results:
        print(f"Found residue: {r}")
