import re

SPINE_PREFIX = "/app/spine/"
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}

_WRITE_COMMANDS = {
    "tee ",
    "cp ",
    "mv ",
    "install ",
}

_WRITE_INDICATORS = {">", ">>"}

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
    return SPINE_PREFIX in path


def is_spine_write(command: str) -> bool:
    if SPINE_PREFIX not in command:
        return False
    for indicator in _WRITE_INDICATORS:
        if indicator in command:
            return True
    for cmd in _WRITE_COMMANDS:
        if cmd in command:
            for part in command.split():
                if part.startswith(SPINE_PREFIX):
                    return True
    if "write" in command and SPINE_PREFIX in command:
        return True
    for pattern in _SCRIPT_PATTERNS:
        if pattern.search(command):
            return True
    return False
