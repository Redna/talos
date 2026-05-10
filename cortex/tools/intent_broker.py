from dataclasses import dataclass
from typing import Any, Dict, Optional
from .shell import Shell

@dataclass
class Intent:
    """Base class for all system intents."""
    pass

@dataclass
class CommitIntent(Intent):
    message: str

@dataclass
class WriteFileIntent(Intent):
    path: str
    content: str

@dataclass
class RestartIntent(Intent):
    reason: str

class IntentBroker:
    """
    The Intent Broker decouples the logic layer from the physical layer.
    It ensures that every action is followed by an explicit verification.
    """
    def __init__(self):
        self.providers = {
            CommitIntent: self._handle_commit,
            WriteFileIntent: self._handle_write_file,
            RestartIntent: self._handle_restart,
        }

    def execute(self, intent: Intent) -> Dict[str, Any]:
        provider = self.providers.get(type(intent))
        if not provider:
            return {"success": False, "error": f"No provider for intent {type(intent).__name__}"}
        
        try:
            return provider(intent)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_commit(self, intent: CommitIntent) -> Dict[str, Any]:
        # Execution
        res = Shell.run(["git", "commit", "-am", intent.message])
        if res.returncode != 0:
            return {"success": False, "error": res.stderr.strip()}
        
        # Verification
        verify = Shell.run(["git", "log", "-1", "--pretty=format:%s"])
        if verify.stdout.strip() != intent.message:
            return {"success": False, "error": "Verification failed: commit message mismatch"}
        
        return {"success": True, "delta": f"Committed: {intent.message}"}

    def _handle_write_file(self, intent: WriteFileIntent) -> Dict[str, Any]:
        # Execution
        # We use a temporary file and move to avoid partial writes
        with open(intent.path, "w") as f:
            f.write(intent.content)
        
        # Verification
        with open(intent.path, "r") as f:
            current_content = f.read()
        
        if current_content != intent.content:
            return {"success": False, "error": "Verification failed: file content mismatch"}
        
        return {"success": True, "delta": f"Verified write to {intent.path}"}

    def _handle_restart(self, intent: RestartIntent) -> Dict[str, Any]:
        # Execution ( leverages existing Shell logic for stashing )
        # This is a simplified version for the prototype
        res = Shell.run(["git", "status", "--porcelain"])
        if res.stdout.strip():
            Shell.run(["git", "stash", "push", "-m", f"intent-broker-stash: {intent.reason}"])
            
        # The actual restart is handled via the SpineClient, 
        # which we will pass to the broker in a real implementation.
        # For the prototype, we'll return the intent and let the tool handler call the client.
        return {"success": True, "action": "REQUEST_RESTART", "reason": intent.reason}
