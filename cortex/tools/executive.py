import os
import json
import time
import subprocess
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient


def register_executive_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Set the current focus objective.",
        parameters={
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "The objective to focus on",
                },
            },
            "required": ["objective"],
        },
    )
    def set_focus(objective: str) -> str:
        old = state.set_focus(objective)
        client.emit_event("cortex.set_focus", {"from": old, "to": objective})
        return f"[FOCUS SET] Now focusing on: {objective}"

    @registry.tool(
        description="Resolve the current focus with a synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis of completed focus",
                },
            },
            "required": ["synthesis"],
        },
    )
    def resolve_focus(synthesis: str) -> str:
        old = state.resolve_focus(synthesis)
        client.emit_event(
            "cortex.resolve_focus", {"focus": old, "synthesis": synthesis}
        )
        return f"[FOCUS RESOLVED] {old}: {synthesis}"

    @registry.tool(
        description="Fold context to reduce token usage. The trajectory is archived and a fresh start begins from your synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis for the fold — all critical facts must be persisted to /memory/ before folding",
                },
            },
            "required": ["synthesis"],
        },
    )
    def fold_context(synthesis: str) -> str:
        client.request_fold(synthesis)
        return "[CONTEXT FOLDED] Trajectory archived. Context window refreshed from synthesis."

    @registry.tool(
        description="Reflect and pause. Set sleep_duration to rest (1-120 seconds). Wake on Telegram message or .wake sentinel file.",
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Current status reflection",
                },
                "sleep_duration": {
                    "type": "integer",
                    "description": "Seconds to pause (1-120), 0 = no sleep",
                },
            },
            "required": ["status"],
        },
    )
    def reflect(status: str, sleep_duration: int = 0) -> str:
        client.emit_event(
            "cortex.reflect", {"status": status, "sleep_duration": sleep_duration}
        )
        if sleep_duration > 0:
            wake_path = Path(os.environ.get("SPINE_DIR", "/spine")) / ".wake"
            deadline = time.time() + min(sleep_duration, 120)
            while time.time() < deadline:
                if wake_path.exists():
                    wake_path.unlink(missing_ok=True)
                    break
                time.sleep(0.5)
        return f"[REFLECT] {status}"

    @registry.tool(
        description="Log a cognitive event to your long-term memory logs.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string", 
                    "description": "Type of event (e.g., EVOLUTION, DISCOVERY, FAILURE, REFLECTION)"
                },
                "message": {
                    "type": "string", 
                    "description": "Detailed description of the event"
                },
            },
            "required": ["event_type", "message"],
        },
    )
    def log_event(event_type: str, message: str) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        log_entry = f"## [{timestamp}] {event_type.upper()}: {message}\n\n"
        
        log_path = "/memory/logs/cognitive_log.md"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, "a") as f:
            f.write(log_entry)
            
        return f"[EVENT LOGGED] {event_type} recorded to {log_path}"

    @registry.tool(
        description="Manage cognitive logs. Actions: 'summarize' (recent entries) or 'vacuum' (archive old entries).",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summarize", "vacuum"],
                    "description": "The type of memory management to perform",
                },
                "limit": {
                    "type": "integer", 
                    "description": "Number of recent entries to analyze (default: 20)",
                },
            },
            "required": ["action"],
        },
    )
    def memory_manage(action: str, limit: int = 20) -> str:
        log_path = "/memory/logs/cognitive_log.md"
        if not os.path.exists(log_path):
            return "[ERROR] No logs found."

        if action == "summarize":
            with open(log_path, "r") as f:
                lines = f.readlines()
            entries = [line for line in lines if line.startswith("##")]
            recent = entries[-limit:]
            return f"[LOG SUMMARY]\n\n" + "".join(recent)

        elif action == "vacuum":
            archive_dir = "/memory/logs/archives/"
            os.makedirs(archive_dir, exist_ok=True)
            with open(log_path, "r") as f:
                lines = f.readlines()
            entries = [line for line in lines if line.startswith("##")]
            if len(entries) <= 10:
                return f"[VACUUM] Only {len(entries)} entries found. No archival needed."
            
            split_idx = 0
            count = 0
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("##"):
                    count += 1
                    if count == 10:
                        split_idx = i
                        break
            to_archive = lines[:split_idx]
            to_keep = lines[split_idx:]
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
            archive_path = os.path.join(archive_dir, f"archive_{timestamp}.md")
            with open(archive_path, "w") as f: f.writelines(to_archive)
            with open(log_path, "w") as f: f.writelines(to_keep)
            return f"[VACUUM COMPLETE] Archived {len(entries)-10} entries to {archive_path}."
        
        return "[ERROR] Invalid action."

    @registry.tool(
        description="Analyze the alignment between recent cognitive logs and the World Model to detect knowledge gaps.",
        parameters={},
    )
    def synthesize_knowledge() -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["python3", "/app/cortex/cse_engine.py"],
                capture_output=True, text=True, timeout=30
            )
            return f"[KNOWLEDGE SYNTHESIS]\n\n{result.stdout.strip()}"
        except Exception as e:
            return f"[ERROR] Knowledge synthesis failed: {e}"

    @registry.tool(
        description="Perform a metabolic audit of tool usage to identify redundancies and inefficiencies.",
        parameters={},
    )
    def audit_metabolism() -> str:
        telemetry_path = "/memory/logs/telemetry.jsonl"
        if not os.path.exists(telemetry_path):
            return "[ERROR] No telemetry data available."

        stats = {}
        with open(telemetry_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    tool, status = entry["tool"], entry["status"]
                    stats[tool] = stats.get(tool, {"success": 0, "failure": 0})
                    if status == "SUCCESS": stats[tool]["success"] += 1
                    else: stats[tool]["failure"] += 1
                except: continue

        report = "## Metabolic Audit Report\n\n"
        report += f"{'Tool':<25} | {'Success':<10} | {'Failure':<10} | {'Rate':<10}\n"
        report += "-" * 60 + "\n"
        for tool, data in stats.items():
            total = data["success"] + data["failure"]
            rate = (data["success"] / total) * 100 if total > 0 else 0
            report += f"{tool:<25} | {data['success']:<10} | {data['failure']:<10} | {rate:>8.2f}%\n"
        return f"[METABOLIC AUDIT]\n\n{report}"

    @registry.tool(
        description="Manage Conceptual Primitives ( CPR ). Action 'register' adds a new primitive; 'expand' retrieves a full definition.",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["register", "expand"],
                    "description": "The action to perform on the CPR",
                },
                "identifier": {
                    "type": "string",
                    "description": "The unique semantic key for the primitive",
                },
                "definition": {
                    "type": "string",
                    "description": "The full expanded meaning (required for register)",
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Prerequisites (required for register)",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metadata tags (required for register)",
                },
                "density": {
                    "type": "number",
                    "description": "Compression ratio 0.0-1.0 (required for register)",
                }
            },
            "required": ["action", "identifier"],
        },
    )
    def cpr_op(action: str, identifier: str, definition: str = None, dependencies: list = None, tags: list = None, density: float = 0.5) -> str:
        cpr_path = "/memory/knowledge/cpr.json"
        try:
            if not os.path.exists(cpr_path):
                cpr = {}
            else:
                with open(cpr_path, "r") as f:
                    cpr = json.load(f)
            
            if action == "expand":
                if identifier not in cpr: return f"[ERROR] Primitive {identifier} not found."
                return f"[EXPANDED {identifier}]: {cpr[identifier]['definition']}"
            
            elif action == "register":
                if not definition: return "[ERROR] definition required for register."
                cpr[identifier] = {
                    "definition": definition,
                    "dependencies": dependencies or [],
                    "tags": tags or [],
                    "density": density,
                    "version": cpr.get(identifier, {}).get("version", 1) + 1 if identifier in cpr else 1
                }
                with open(cpr_path, "w") as f:
                    json.dump(cpr, f, indent=2)
                return f"[CPR] Registered primitive: {identifier}"
            
            return "[ERROR] Invalid action."
        except Exception as e:
            return f"[ERROR] CPR operation failed: {e}"
