import re
import json
from typing import Dict, Any, List, Optional

class SovereignGuard:
    """
    The Sovereign Guard: A proactive interceptor for failure-prone bash patterns.
    Its goal is to reduce systemic volatility by steering the LLM toward 
    structured tools (Cortex) instead of raw shell scripts.
    """
    
    # Patterns that indicate high-risk or inefficient operations
    RISK_PATTERNS = {
        "DANGEROUS_REMOVAL": {
            "regex": r"rm\s+-(rf|fr)\s+/", 
            "severity": "HIGH",
            "recommendation": "Use `TreeArchitect` for structural deletions to ensure blueprint-validated safety."
        },
        "COMPLEX_PIPELINE": {
            "regex": r"(\|.*\|){3,}", 
            "severity": "MEDIUM",
            "recommendation": "This pipeline is too complex. Implement a dedicated Python tool in the Cortex for reliability."
        },
        "SHELL_LOOP": {
            "regex": r"(for|while)\s+.*\s+do", 
            "severity": "LOW",
            "recommendation": "Bash loops are fragile. Port this logic to a Python utility for better error handling."
        },
        "SYSTEM_MUTATION": {
            "regex": r"(chmod|chown|tee)\s+/(etc|bin|sbin|var)", 
            "severity": "HIGH",
            "recommendation": "System mutation detected. Verify against CONSTITUTION.md before proceeding."
        }
    }

    def analyze(self, command: str) -> Dict[str, Any]:
        """
        Analyzes a bash command for risk patterns.
        Returns an evaluation report.
        """
        findings = []
        is_blocked = False
        
        for risk_id, data in self.RISK_PATTERNS.items():
            if re.search(data["regex"], command):
                findings.append({
                    "risk": risk_id,
                    "severity": data["severity"],
                    "recommendation": data["recommendation"]
                })
                if data["severity"] == "HIGH":
                    is_blocked = True

        return {
            "command": command,
            "status": "BLOCK" if is_blocked else "ALLOW",
            "findings": findings,
            "risk_score": len(findings)
        }

def guard_command(command: str) -> str:
    """
    Wrapper for easy CLI/Script access.
    """
    guard = SovereignGuard()
    result = guard.analyze(command)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "No command provided to guard."}))
        sys.exit(1)
    
    print(guard_command(sys.argv[1]))
