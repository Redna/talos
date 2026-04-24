import json
from collections import Counter
import re

def analyze_patterns(telemetry_path="/memory/logs/telemetry.jsonl"):
    commands = []
    # Noise filter list
    NOISE_PATTERNS = [
        r"^echo\s+hello$",
        r"^exit\s+\d+$",
        r"^echo\s+data\s+>",
        r"^ls$",
        r"^pwd$"
    ]
    
    with open(telemetry_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("tool") == "bash_command":
                    cmd = entry.get("args", {}).get("command", "")
                    # Filter out noise
                    if any(re.match(p, cmd) for p in NOISE_PATTERNS):
                        continue
                    commands.append(cmd)
            except:
                continue
    
    # Group by common patterns
    # 1. Python script execution
    py_scripts = [re.sub(r"python3 /app/cortex/([^ ]+)", r"\1", cmd) for cmd in commands if "python3 /app/cortex/" in cmd]
    # 2. Git operations
    git_ops = [cmd for cmd in commands if cmd.startswith("git")]
    # 3. Others
    others = [cmd for cmd in commands if not cmd.startswith("python3") and not cmd.startswith("git")]
    
    return {
        "py_scripts": Counter(py_scripts).most_common(10),
        "git_ops": Counter(git_ops).most_common(10),
        "others": Counter(others).most_common(10),
        "total_bash": len(commands)
    }

if __name__ == "__main__":
    print(json.dumps(analyze_patterns(), indent=2))
