import re
from pathlib import Path

SPINE_PREFIX = "/app/spine/"
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}

_WRITE_COMMANDS = {
    "tee ",
    "cp ",
    "mv ",
    "install ",
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
    resolved = Path(path).resolve()
    try:
        return resolved.is_relative_to(Path("/app/spine").resolve())
    except (OSError, ValueError):
        return str(resolved).startswith(SPINE_PREFIX)


def is_spine_write(command: str) -> bool:
    if SPINE_PREFIX not in command:
        return False
    for indicator in (">", ">>"):
        if indicator in command:
            for part in command.split():
                if part.startswith(SPINE_PREFIX):
                    return True
    for cmd in _WRITE_COMMANDS:
        if cmd in command:
            for part in command.split():
                if part.startswith(SPINE_PREFIX):
                    return True
    for pattern in _SCRIPT_PATTERNS:
        if pattern.search(command):
            return True
    return False
