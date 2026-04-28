import re
from pathlib import Path
import subprocess

PROTECTED_CORTEX_FILES = {
    "/app/cortex/spine_client.py",
}
BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}
IDENTITY_FILES = {"CONSTITUTION.md", "identity.md"}

DANGEROUS_PATTERNS = [
    # Recursive root deletion
    re.compile(r"rm\s+.*-(rf|fr)\s+/(?:\s|$)"),
    # Filesystem creation
    re.compile(r"mkfs\."),
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


def is_protected_cortex_file(path: str) -> bool:
    """Check if a path targets a cortex file that the agent must not modify."""
    if not path:
        return False
    try:
        resolved = str(Path(path).resolve())
        return resolved in PROTECTED_CORTEX_FILES
    except (OSError, ValueError):
        return path in PROTECTED_CORTEX_FILES


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

    # 1. Identity Core Protection (Ship of Theseus)
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
