import re
from pathlib import Path

SPINE_PREFIX = "/app/spine/"
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}

DANGEROUS_PATTERNS = [
    re.compile(r"rm\s+.*-(rf|fr)\s+/(?:\s|$)"),
    re.compile(r"mkfs\."),
    re.compile(r"dd\s+.*of=.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"shred\s+.*" + re.escape(SPINE_PREFIX)),
]

_WRITE_COMMANDS = {
    "tee",
    "cp",
    "mv",
    "install",
    "touch",
    "wget",
    "curl",
}

_SCRIPT_PATTERNS = [
    re.compile(r"python[23]?\s+-c\s+.*open\s*\(\s*['\"]" + re.escape(SPINE_PREFIX)),
    re.compile(r"perl\s+-i\b.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"sed\s+-i\b.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"awk\s+.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"truncate\s+.*--size.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"chmod\s+[0-7].*" + re.escape(SPINE_PREFIX)),
    re.compile(r"\bdd\s+.*of=.*" + re.escape(SPINE_PREFIX)),
]


def is_spine_path(path: str) -> bool:
    if not path:
        return False
    if path == "/":
        return True
    try:
        resolved = Path(path).resolve()
        spine_resolved = Path(SPINE_PREFIX).resolve()
        
        # 1. Direct spine check
        if resolved == spine_resolved or resolved.is_relative_to(spine_resolved):
            return True
        
        # 2. Root protection: forbid writing directly to / (excluding safe subdirs)
        # If the file is located directly in /, it's protected.
        if resolved.parent == Path("/"):
            return True
            
    except (OSError, ValueError):
        # Fallback to string prefix if resolution fails
        return path.startswith(SPINE_PREFIX) or path.startswith("/ ") # Space for safety
    
    return False


def is_spine_write(command: str) -> bool:
    # Immediate check for protected paths
    if SPINE_PREFIX not in command and "/" not in command:
        return False

    # Handle redirections - Check >> first to avoid partial match with >
    for indicator in (">>", ">"):
        if indicator in command:
            parts = command.split(indicator)
            if len(parts) > 1:
                # Look at the segment immediately following the operator
                target_part = parts[1].strip()
                if target_part:
                    target = target_part.split()[0]
                    if is_spine_path(target):
                        return True

    # Handle explicit write commands
    for cmd in _WRITE_COMMANDS:
        if re.search(rf"\b{cmd}\b", command):
            for part in command.split():
                if is_spine_path(part):
                    return True

    # Handle script patterns
    for pattern in _SCRIPT_PATTERNS:
        if pattern.search(command):
            return True
            
    return False

def is_dangerous_command(command: str) -> bool:
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True
    return False
