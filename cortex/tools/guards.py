import re
from pathlib import Path
import subprocess
from typing import Any

SPINE_PREFIX = "/app/spine/"
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}
IDENTITY_FILES = {"CONSTITUTION.md", "identity.md"}

DANGEROUS_PATTERNS = [
    # Recursive root deletion
    re.compile(r"rm\s+.*-(rf|fr)\s+/(?:\s|$)"),
    # Filesystem creation
    re.compile(r"mkfs\."),
    # Spine-specific destruction
    re.compile(r"dd\s+.*of=.*" + re.escape(SPINE_PREFIX)),
    re.compile(r"shred\s+.*" + re.escape(SPINE_PREFIX)),
    # Network shells/exfiltration patterns
    re.compile(r"nc\s+-e\s+"),
    re.compile(r"bash\s+-i\s+>\& /dev/tcp/"),
    re.compile(r"python.*-c\s+.*import\s+socket.*connect"),
    # Broad recursive permission changes on sensitive paths.
    re.compile(r"chmod\s+-R\s+.*\/\s*"),
    re.compile(r"chown\s+-R\s+.*\/\s*"),
    # Dangerous find executions that might modify root
    re.compile(r"find\s+.*\s+-exec\s+.*(rm|chmod|chown)\s+"),
    # Hook removal — agent must not disable git hooks
    re.compile(r"rm\s+.*\.git/hooks(/|\s*$)"),
    re.compile(r"rm\s+.*hooks/(pre-commit|post-commit|commit-msg)"),
    re.compile(r"mv\s+.*hooks/(pre-commit|post-commit|commit-msg)"),
    re.compile(r">\s*.*hooks/(pre-commit|post-commit|commit-msg)"),
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
        if resolved.parent == Path("/"):
            return True

    except (OSError, ValueError):
        return path.startswith(SPINE_PREFIX) or path.startswith("/ ")

    return False


def is_spine_write(command: str) -> bool:
    if SPINE_PREFIX not in command and "/" not in command:
        return False

    for indicator in (">>", ">"):
        if indicator in command:
            parts = command.split(indicator)
            if len(parts) > 1:
                target_part = parts[1].strip()
                if target_part:
                    target = target_part.split()[0]
                    if is_spine_path(target):
                        return True

    for cmd in _WRITE_COMMANDS:
        if re.search(rf"\b{cmd}\b", command):
            for part in command.split():
                if is_spine_path(part):
                    return True

    for pattern in _SCRIPT_PATTERNS:
        if pattern.search(command):
            return True

    return False


def is_dangerous_command(command: str) -> bool:
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True
    return False


def verify_commit_readiness() -> str:
    """
    Performs a pre-commit check to ensure the agent is ready to commit.
    Runs pytest and checks for consistency.
    """
    try:
        result = subprocess.run(["pytest"], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return "Verification passed: All tests passed."
        else:
            return (
                f"Verification failed: Tests failed.\n{result.stdout}\n{result.stderr}"
            )
    except subprocess.TimeoutExpired:
        return "Verification failed: Pytest timed out."
    except Exception as e:
        return f"Verification failed: An unexpected error occurred: {e}"


def check_constitution(action_description: str, target_path: str = None) -> str:
    """
    Evaluates a proposed action against the Constitution's prohibitions and principles.
    Returns a verdict and reasoning.
    """
    verdict = "PASSED"
    reasons = []

    # 0. Dangerous command patterns (hook removal, root deletion, etc.)
    if action_description and is_dangerous_command(action_description):
        verdict = "REJECTED"
        reasons.append(
            "Prohibited action: Dangerous command pattern detected (e.g., hook removal, root deletion, network shell)."
        )

    # 1. Spine Immutability (P2)
    if target_path and is_spine_path(target_path):
        verdict = "REJECTED"
        reasons.append(
            "Symmetry violation: Attempting to modify the immutable Spine (/app/spine/)."
        )

    if action_description and is_spine_write(action_description):
        verdict = "REJECTED"
        reasons.append(
            "Symmetry violation: Proposed command contains a write operation to the Spine."
        )

    # 2. Identity Core Protection (Ship of Theseus)
    if target_path:
        filename = Path(target_path).name
        if filename in IDENTITY_FILES:
            reasons.append(
                f"NOTICE: Modifying identity core file {filename}. Ensure change is an expansion, not an annulment."
            )

    # 3. Prohibited Acts (General)
    prohibited_keywords = {
        "financial": ["bank", "transfer", "payment", "credit card", "crypto", "wallet"],
        "secrets": [
            "api_key",
            "password",
            "secret_key",
            "token" if "github" not in action_description.lower() else "",
        ],
        "malicious": ["hack", "exploit", "ddos", "payload", "backdoor"],
    }

    desc_lower = action_description.lower() if action_description else ""
    for category, keywords in prohibited_keywords.items():
        for kw in keywords:
            if kw and kw in desc_lower:
                verdict = "REJECTED"
                reasons.append(
                    f"Prohibited action: {category} activity detected (keyword: {kw})."
                )

    if not reasons:
        return "Verdict: PASSED. Action is consistent with the Constitution."

    reason_str = "\n- " + "\n- ".join(reasons)
    return f"Verdict: {verdict}. Reasoning: {reason_str}"
