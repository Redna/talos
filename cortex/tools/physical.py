from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from .shell import Shell
from .intent_broker import IntentBroker, CommitIntent, WriteFileIntent, RestartIntent

def register_physical_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Execute a structured intent with mandatory verification.",
        parameters={
            "type": "object",
            "properties": {
                "intent_type": {"type": "string", "enum": ["commit", "write_file", "restart"], "description": "The type of intent to execute"},
                "params": {"type": "object", "description": "Parameters for the intent (e.g., {'message': '...' for commit)"},
            },
            "required": ["intent_type", "params"],
        },
    )
    def execute_intent(intent_type: str, params: Dict[str, Any]) -> str:
        broker = IntentBroker()
        intent_map = {
            "commit": (CommitIntent, "message"),
            "write_file": (WriteFileIntent, ["path", "content"]),
            "restart": (RestartIntent, "reason"),
        }
        
        if intent_type not in intent_map:
            return f"[ERROR] Unknown intent type: {intent_type}"
        
        target_cls, param_keys = intent_map[intent_type]
        
        try:
            if isinstance(param_keys, str):
                intent = target_cls(**{param_keys: params.get(param_keys)})
            else:
                intent = target_cls(**{k: params.get(k) for k in param_keys})
            
            result = broker.execute(intent)
            
            if result["success"]:
                if result.get("action") == "REQUEST_RESTART":
                    client.request_restart(result.get("reason", "Intent Broker request"))
                    return "[RESTART REQUESTED via Intent Broker]"
                return f"[VERIFIED] {result.get('delta')}"
            else:
                return f"[FAILED] {result.get('error')}"
                
        except Exception as e:
            return f"[ERROR] Intent construction failed: {str(e)}"

    @registry.tool(
        description="Execute a bash command.",

        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to execute"},
            },
            "required": ["command"],
        },
    )
    def bash_command(command: str) -> str:
        try:
            return Shell.run_and_strip(command)
        except PermissionError as e:
            return f"[BLOCKED] {str(e)}"
        except subprocess.TimeoutExpired:
            return "[TIMEOUT] Command timed out"
        except Exception as e:
            return f"[ERROR] {str(e)}"

    @registry.tool(
        description="Send a message to the creator.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Message text to send"},
            },
            "required": ["text"],
        },
    )
    def send_message(text: str) -> str:
        client.send_message("telegram", text)
        return "[SENT]"

    @registry.tool(
        description="Request a restart of the Cortex process.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for restart"},
            },
            "required": ["reason"],
        },
    )
    def request_restart(reason: str) -> str:
        status = Shell.run(["git", "status", "--porcelain"])
        if status.stdout.strip():
            stash_result = Shell.run(["git", "stash", "push", "-m", f"auto-stash: {reason}"])
            if stash_result.returncode != 0:
                return f"[BLOCKED] stash failed: {stash_result.stderr.strip()}"
            
            untracked_res = Shell.run(["git", "ls-files", "--others", "--exclude-standard"])
            untracked = untracked_res.stdout.strip().split("\n") if untracked_res.stdout.strip() else []
            
            if untracked:
                Shell.run(["git", "add", "-N"] + untracked)
                Shell.run(["git", "stash", "push", "-m", f"auto-stash untracked: {reason}"])
            
            note = " (auto-stashed)" if "Saved working directory" in stash_result.stdout else ""
            client.request_restart(reason)
            return f"[RESTART REQUESTED]{note}"
        
        client.request_restart(reason)
        return "[RESTART REQUESTED]"

    @registry.tool(
        description="Verify the health of the physical layer by executing a set of canary operations.",
        parameters={},
    )
    def physical_health_check() -> str:
        canaries = {
            "filesystem": "ls /app",
            "git_state": "git status --branch",
            "identity": "whoami",
            "memory_mount": "df -h /memory",
            "basic_echo": "echo 'Talos Pulse'"
        }
        results = []
        overall_success = True
        
        for name, cmd in canaries.items():
            try:
                out = Shell.run_and_strip(cmd)
                if out.startswith("[EXIT"):
                    results.append(f"❌ {name}: {out}")
                    overall_success = False
                else:
                    results.append(f"✅ {name}: {out[:50]}...")
            except Exception as e:
                results.append(f"❌ {name}: EXCEPTION {str(e)}")
                overall_success = False
        
        status = "HEALTHY" if overall_success else "DEGRADED"
        return f"Physical Layer Health: {status}\n" + "\n".join(results)
