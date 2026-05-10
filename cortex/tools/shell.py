import subprocess
from typing import List

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}

class Shell:
    """
    Encapsulates all physical shell interactions to prevent logic-layer leakage.
    """
    @staticmethod
    def run(command: str | List[str], input_str: str = None, cwd: str = None, timeout: int = 60) -> subprocess.CompletedProcess:
        if isinstance(command, str):
            for flag in BLOCKED_FLAGS:
                if flag in command:
                    raise PermissionError(f"Flag {flag} is not allowed")
            
            return subprocess.run(
                command,
                shell=True,
                input=input_str,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            # For list-based commands
            return subprocess.run(
                command,
                shell=False,
                input=input_str,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

    @staticmethod
    def run_and_strip(command: str, timeout: int = 60) -> str:
        res = Shell.run(command, timeout=timeout)
        if res.returncode != 0:
            return f"[EXIT {res.returncode}] {res.stderr.strip()}"
        return res.stdout.strip() or "[OK]"
