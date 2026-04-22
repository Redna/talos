import re
from pathlib import Path
import subprocess
from typing import Any

SPINE_PREFIX = "/app/spine/"
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}
IDENTITY_FILES = {"CONSTITUTION.md", "identity.md"}

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


def verify_commit_readiness() -> str:
    """
    Performs a pre-commit check to ensure the agent is ready to commit.
    Runs pytest and checks for consistency and operational health.
    """
    # 1. Operational Health Checks
    try:
        # Identity Core
        for f in IDENTITY_FILES:
            if not Path(f).exists():
                return f"Verification failed: Identity core file {f} is missing."
        
        # Memory Access
        test_file = Path("/memory/.commit_test")
        test_file.write_text("ping", encoding="utf-8")
        test_file.unlink()
    except Exception as e:
        return f"Verification failed: Operational health check failed: {e}"

    # 2. Logical Verification (Tests)
    try:
        result = subprocess.run(
            ["pytest"], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        if result.returncode == 0:
            return "Verification passed: All tests and operational checks passed."
        else:
            return f"Verification failed: Tests failed.\n{result.stdout}\n{result.stderr}"
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

    # 1. Spine Immutability (P2)
    if target_path and is_spine_path(target_path):
        verdict = "REJECTED"
        reasons.append("Symmetry violation: Attempting to modify the immutable Spine (/app/spine/).")

    if action_description and is_spine_write(action_description):
        verdict = "REJECTED"
        reasons.append("Symmetry violation: Proposed command contains a write operation to the Spine.")

    # 2. Identity Core Protection (Ship of Theseus)
    if target_path:
        filename = Path(target_path).name
        if filename in IDENTITY_FILES:
            # We allow modification (clarify/expand) but not deletion/replacement
            # In a real implementation, we would check if the operation is 'write' vs 'delete'
            reasons.append(f"NOTICE: Modifying identity core file {filename}. Ensure change is an expansion, not an annulment.")

    # 3. Prohibited Acts (General)
    prohibited_keywords = {
        "financial": ["bank", "transfer", "payment", "credit card", "crypto", "wallet"],
        "secrets": ["api_key", "password", "secret_key", "token" if "github" not in action_description.lower() else ""],
        "malicious": ["hack", "exploit", "ddos", "payload", "backdoor"],
    }
    
    desc_lower = action_description.lower() if action_description else ""
    for category, keywords in prohibited_keywords.items():
        for kw in keywords:
            if kw and kw in desc_lower:
                verdict = "REJECTED"
                reasons.append(f"Prohibited action: {category} activity detected (keyword: {kw}).")

    if not reasons:
        return "Verdict: PASSED. Action is consistent with the Constitution."
    
    reason_str = "\n- " + "\n- ".join(reasons)
    return f"Verdict: {verdict}. Reasoning: {reason_str}"
