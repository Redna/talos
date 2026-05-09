import os
import time
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
        protected=True,
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
        description="Fold context to reduce token usage. The trajectory is archived and a fresh start begins from your structured handover.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Autopsy: 1. State Delta (what was done), 2. Negative Knowledge (what failed/avoid).",
                },
                "current_focus": {
                    "type": "string",
                    "description": "The exact objective you are actively trying to complete right now.",
                },
                "active_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific file paths you need immediate access to post-fold.",
                },
                "next_action": {
                    "type": "string",
                    "description": "The exact first tool call or step you will take after the fold.",
                },
            },
            "required": ["synthesis", "current_focus", "active_files", "next_action"],
        },
        protected=True,
    )
    def fold_context(synthesis: str, current_focus: str, active_files: list, next_action: str) -> str:
        client.request_fold(synthesis, current_focus, active_files, next_action)
        return (
            f"[SUCCESS] Context successfully folded. HUD budget restored to optimal levels. "
            f"Cognitive load minimized. Resuming with focus: {current_focus}"
        )

    @registry.tool(
        description="Reflect and pause. Set sleep_duration to rest (1-1800 seconds, max 30 minutes). Wake on Telegram message or .wake sentinel file.",
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Current status reflection",
                },
                "sleep_duration": {
                    "type": "integer",
                    "description": "Seconds to pause (1-1800, max 30 min), 0 = no sleep",
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
            spine_dir = os.environ.get("SPINE_DIR", "/spine")
            wake_path = Path(spine_dir) / "events" / ".wake"
            deadline = time.time() + min(sleep_duration, 1800)
            next_heartbeat = time.time() + 30
            while time.time() < deadline:
                if wake_path.exists():
                    try:
                        wake_path.unlink(missing_ok=True)
                    except PermissionError:
                        pass
                    break
                if time.time() >= next_heartbeat:
                    client.emit_event(
                        "cortex.reflect_heartbeat",
                        {"remaining": int(deadline - time.time())},
                    )
                    next_heartbeat = time.time() + 30
                time.sleep(0.5)
        return f"[REFLECT] {status}"

    @registry.tool(
        description="Merge multiple memory files into one. The tool reads all sources, synthesizes them via an isolated LLM call, writes the result, deletes the originals, and updates memory_index.md.",
        parameters={
            "type": "object",
            "properties": {
                "source_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths to merge (relative to /memory/)",
                },
                "destination_file": {
                    "type": "string",
                    "description": "Output file path (relative to /memory/)",
                },
                "synthesis_focus": {
                    "type": "string",
                    "description": "What topic or theme to focus the synthesis on",
                },
            },
            "required": ["source_files", "destination_file", "synthesis_focus"],
        },
    )
    def merge_memory_files(source_files: list, destination_file: str, synthesis_focus: str) -> str:
        import os as _os
        mem_dir = Path(_os.environ.get("MEMORY_DIR", "/memory"))

        # 1. Read all source files
        contents = {}
        for fname in source_files:
            fpath = mem_dir / fname
            if not fpath.exists():
                return f"[ERROR] Source file not found: {fname}"
            try:
                contents[fname] = fpath.read_text()
            except Exception as e:
                return f"[ERROR] Failed to read {fname}: {e}"

        # 2. Build synthesis prompt
        combined = "\n\n---\n\n".join(
            f"### {name}\n{text}" for name, text in contents.items()
        )
        prompt = (
            f"You are a summarization function. Read these documents and synthesize "
            f"all non-redundant facts, architectural decisions, and rules into a single "
            f"markdown document focused on: {synthesis_focus}.\n\n"
            f"{combined}"
        )

        # 3. Isolated LLM call for synthesis
        try:
            import subprocess, json as _json
            gate_url = _os.environ.get("GATE_URL", "http://gate:4000/v1/chat/completions")
            payload = {
                "model": _os.environ.get("TALOS_MODEL", "gemma4"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "temperature": 0.3,
            }
            result = subprocess.run(
                ["curl", "-s", gate_url, "-H", "Content-Type: application/json", "-d", _json.dumps(payload)],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return f"[ERROR] Synthesis LLM call failed: {result.stderr}"
            resp = _json.loads(result.stdout)
            synthesis = resp["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[ERROR] Synthesis failed: {e}"

        # 4. Write destination
        dest_path = mem_dir / destination_file
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(synthesis)

        # 5. Delete originals
        deleted = []
        for fname in source_files:
            try:
                (mem_dir / fname).unlink()
                deleted.append(fname)
            except Exception as e:
                return f"[ERROR] Failed to delete {fname} after merge: {e}"

        # 6. Update index
        index_path = mem_dir / "memory_index.md"
        note = f"- {destination_file}: merged {len(source_files)} files ({synthesis_focus})\n"
        with open(index_path, "a") as f:
            f.write(note)

        return (
            f"[SUCCESS] {len(source_files)} files merged into {destination_file}. "
            f"Original files deleted: {', '.join(deleted)}. Memory index updated."
        )
