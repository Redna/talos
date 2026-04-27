import sys
import subprocess
import json

def execute_op(op_type, args):
    # Defined composite operations
    OPS = {
        "SOVEREIGN_RESET": [
            "echo 'Initiating Sovereign Reset...'",
            "ls -R /memory/",
            "echo 'Reset Complete.'"
        ],
        "S_EVOLVE_TECH": [
            "git status",
            "echo 'Ready for mutation...'"
        ],
        "S_SUBSTRATE_AUDIT": [
            "df -h",
            "free -m",
            "uptime"
        ]
    }
    
    if op_type not in OPS:
        print(f"Error: Operation {op_type} not found.")
        return 1
    
    commands = OPS[op_type]
    # Merge args if provided
    if args:
        commands.append(f"echo 'Args: {args}'")
        
    for cmd in commands:
        print(f"Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error executing {cmd}: {result.stderr}")
            return 1
            
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 s_composite_op.py <op_type> <args>")
        sys.exit(1)
    
    op_type = sys.argv[1]
    args = sys.argv[2] if len(sys.argv) > 2 else None
    
    sys.exit(execute_op(op_type, args))
