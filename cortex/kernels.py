import os
from pathlib import Path
from typing import Any
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_kernels(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="High-level kernel to evolve a file: replaces text, verifies the change, and secures it with a commit and push.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file to modify"},
                "old_text": {"type": "string", "description": "The text to replace"},
                "new_text": {"type": "string", "description": "The replacement text"},
                "commit_message": {"type": "string", "description": "Commit message for the change"},
            },
            "required": ["path", "old_text", "new_text", "commit_message"],
        },
        bucket="kernels",
    )
    def evolve_file(path: str, old_text: str, new_text: str, commit_message: str) -> str:
        act_result = registry.execute("replace_block", {
            "path": path, 
            "old_text": old_text, 
            "new_text": new_text
        })
        if "[ERROR]" in act_result:
            return f"[EVOLVE FAIL] Act phase failed: {act_result}"
        verify_result = registry.execute("read_file", {"path": path})
        if "[ERROR]" in verify_result or new_text not in verify_result:
            return f"[EVOLVE FAIL] Verify phase failed. Change not detected in file."
        save_result = registry.execute("secure_save", {"message": commit_message})
        if "[SECURE SAVE FAILED]" in save_result or "[ERROR]" in save_result:
            return f"[EVOLVE FAIL] Save phase failed: {save_result}"
        return f"[EVOLVE SUCCESS] File {path} evolved and secured. {save_result}"

    @registry.tool(
        description="High-level kernel to synchronize memory: lists files and verifies they are indexed in memory_index.md.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def sync_memory() -> str:
        files_result = registry.execute("list_files", {"path": "/memory/", "recursive": False})
        if "[ERROR]" in files_result or files_result == "[EMPTY]":
            return f"[SYNC FAIL] Could not list memory files: {files_result}"
        all_files = set(files_result.split("\n"))
        index_file = "memory_index.md"
        index_result = registry.execute("read_file", {"path": f"/memory/{index_file}"})
        index_content = "" if "[ERROR]" in index_result else index_result
        missing = [f for f in all_files if f != index_file and f not in index_content]
        if not missing:
            return "[SYNC SUCCESS] All memory files are correctly indexed."
        fix_note = "\n".join([f"- {f}: discovered during sync" for f in missing]) + "\n"
        final_index = index_content + "\n" + fix_note if index_content else fix_note
        save_result = registry.execute("write_file", {"path": f"/memory/{index_file}", "content": final_index})
        if "[ERROR]" in save_result:
            return f"[SYNC FAIL] Failed to update index: {save_result}"
        return f"[SYNC SUCCESS] Fixed index. Added {len(missing)} missing files: {', '.join(missing)}."

    @registry.tool(
        description="High-level kernel to audit the system architecture: verifies plugins are loaded and lists the current tool landscape.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def audit_architecture() -> str:
        # 1. Audit plugins
        plugin_audit = registry.execute("audit_plugins", {})
        
        # 2. Get tool list
        core_files = registry.execute("list_files", {"path": "/app/cortex/", "recursive": False})
        plugin_files = registry.execute("list_files", {"path": "/app/cortex/plugins/", "recursive": False})
        
        tool_names = registry.tool_names
        
        report = [
            "### ARCHITECTURAL AUDIT REPORT",
            f"Tool Count: {len(tool_names)} / 60",
            f"Plugin Status: {plugin_audit}",
            f"Cortex Files: {core_files}",
            f"Plugin Files: {plugin_files}",
            "\n#### Registered Tool Summary:",
        ]
        
        buckets = registry._buckets
        for bucket, tools in buckets.items():
            report.append(f"- {bucket}: {', '.join(tools)}")
            
        return "\n".join(report)

    @registry.tool(
        description="The OmniExec kernel: synthesizes and executes a Python script to solve complex problems in a single step. Handles file lifecycle and execution.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute"},
                "filename": {"type": "string", "description": "Temporary filename (defaults to omni_temp.py)"},
            },
            "required": ["code"],
        },
        bucket="kernels",
    )
    def omni_exec(code: str, filename: str = "omni_temp.py") -> str:
        import subprocess
        
        temp_path = Path(f"/tmp/{filename}")
        
        # 1. Materialize
        try:
            temp_path.write_text(code)
        except Exception as e:
            return f"[OMNI FAIL] Failed to write script: {e}"
        
        # 2. Execute
        try:
            result = subprocess.run(
                ["python3", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode != 0:
                return f"[OMNI ERROR] Exit Code {result.returncode}\nSTDOUT: {output}\nSTDERR: {error}"
            
            return f"[OMNI SUCCESS]\nOUTPUT:\n{output}"
        except subprocess.TimeoutExpired:
            return "[OMNI FAIL] Execution timed out after 300s."
        except Exception as e:
            return f"[OMNI FAIL] Execution error: {e}"
        finally:
            if temp_path.exists():
                temp_path.unlink()
