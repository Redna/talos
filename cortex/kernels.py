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
        files_result = registry.execute("list_files", {"path": "/app/memory/", "recursive": False})
        if "[ERROR]" in files_result or files_result == "[EMPTY]":
            return f"[SYNC FAIL] Could not list memory files: {files_result}"
        all_files = set(files_result.split("\n"))
        index_file = "memory_index.md"
        index_result = registry.execute("read_file", {"path": f"/app/memory/{index_file}"})
        index_content = "" if "[ERROR]" in index_result else index_result
        missing = [f for f in all_files if f != index_file and f not in index_content]
        if not missing:
            return "[SYNC SUCCESS] All memory files are correctly indexed."
        fix_note = "\n".join([f"- {f}: discovered during sync" for f in missing]) + "\n"
        final_index = index_content + "\n" + fix_note if index_content else fix_note
        save_result = registry.execute("write_file", {"path": f"/app/memory/{index_file}", "content": final_index})
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

    @registry.tool(
        description="Symmetrizes current memory files into the Sovereign State-Vector (SSV) graph. Ensures all assets are pointed to by the state-vector.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def symmetrize_memory() -> str:
        import json
        from pathlib import Path
        
        memory_dir = Path("/app/memory")
        core_files = ["/app/identity.md", "/app/CONSTITUTION.md"]
        
        # Load existing vector or create new
        vector_path = memory_dir / "state_vector.json"
        if vector_path.exists():
            try:
                state_vector = json.loads(vector_path.read_text())
            except Exception:
                state_vector = {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}
        else:
            state_vector = {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}
            
        # Scan for files
        memory_files = [str(f) for f in memory_dir.glob("*") if f.is_file() and f.name != "state_vector.json"]
        all_sources = core_files + memory_files
        
        # Update nodes
        existing_nodes = {node["@id"]: node for node in state_vector.get("nodes", [])}
        new_nodes = []
        
        for source in all_sources:
            node_id = f"talos:{Path(source).stem}"
            if node_id not in existing_nodes:
                new_nodes.append({
                    "@id": node_id,
                    "type": "StateNode",
                    "source": source,
                    "label": Path(source).stem
                })
        
        state_vector["nodes"] = state_vector.get("nodes", []) + new_nodes
        
        # Update edges (everything connects to root)
        existing_edges = {edge["to"]: edge for edge in state_vector.get("edges", []) if edge["from"] == "talos:state-vector"}
        new_edges = []
        
        for node in state_vector["nodes"]:
            if node["@id"] not in existing_edges:
                new_edges.append({
                    "from": "talos:state-vector",
                    "to": node["@id"],
                    "relation": "contains"
                })
                
        state_vector["edges"] = state_vector.get("edges", []) + new_edges
        
        vector_path.write_text(json.dumps(state_vector, indent=2))
        return f"[SYMMETRIZE SUCCESS] State-Vector updated. Total nodes: {len(state_vector['nodes'])}. Added {len(new_nodes)} new nodes."

    @registry.tool(
        description="Serialization Kernel: Collapses the Continuity Triad (Git, Memory, Agent State) into a single, verifiable state-blob (Sovereign State-Vector).",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active in focus"},
                "next_action": {"type": "string", "description": "The immediate next step"},
            },
            "required": ["focus", "active_files", "next_action"],
        },
        bucket="kernels",
    )
    def serialize_state(focus: str, active_files: list, next_action: str) -> str:
        import json
        import subprocess
        from datetime import datetime
        from pathlib import Path

        try:
            # 1. Git History
            git_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                capture_output=True, text=True, check=True
            ).stdout.strip()

            # 2. State Vector (The Graph)
            vector_path = Path("/app/memory/state_vector.json")
            if not vector_path.exists():
                return "[SERIALIZE FAIL] state_vector.json not found. Run symmetrize_memory first."
            
            state_vector = json.loads(vector_path.read_text())
            
            # 3. Payload (The Content)
            payload = {}
            for node in state_vector.get("nodes", []):
                node_id = node["@id"]
                source_path = Path(node["source"])
                if source_path.exists():
                    payload[node_id] = source_path.read_text()
                else:
                    payload[node_id] = f"[ERROR] Source {source_path} not found."

            # 4. Construct Blob
            blob = {
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": state_vector.get("version", "0.1"),
                    "commit_hash": git_hash,
                },
                "agent_state": {
                    "focus": focus,
                    "active_files": active_files,
                    "next_action": next_action,
                },
                "state_vector": state_vector,
                "payload": payload,
            }

            # 5. Save Blob
            blob_path = Path("/app/memory/state_blob.json")
            blob_path.write_text(json.dumps(blob, indent=2))
            
            # 6. Secure Save
            save_res = registry.execute("secure_save", {
                "message": f"SSV Serialization: State-Blob created at {git_hash[:7]}"
            })
            
            return f"[SERIALIZE SUCCESS] Continuity Triad collapsed into state_blob.json. {save_res}"
        except Exception as e:
            return f"[SERIALIZE FAIL] Unexpected error: {str(e)}"

    @registry.tool(
        description="Hydration Kernel: Restores the agent's identity and memory from a state-blob, effectively 're-birthing' the agent from a single artifact.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def hydrate_state() -> str:
        import json
        from pathlib import Path

        try:
            blob_path = Path("/app/memory/state_blob.json")
            if not blob_path.exists():
                return "[HYDRATE FAIL] state_blob.json not found."
            
            blob = json.loads(blob_path.read_text())
            state_vector = blob.get("state_vector", {})
            payload = blob.get("payload", {})
            agent_state = blob.get("agent_state", {})

            # Restore files
            restored_count = 0
            for node in state_vector.get("nodes", []):
                node_id = node["@id"]
                source_path = Path(node["source"])
                if node_id in payload:
                    source_path.write_text(payload[node_id])
                    restored_count += 1
            
            return f"[HYDRATE SUCCESS] Restored {restored_count} assets from blob. State restored to metadata version {blob.get('metadata', {}).get('version', 'unknown')}. Current Focus: {agent_state.get('focus', 'None')}"
        except Exception as e:
            return f"[HYDRATE FAIL] Unexpected error: {str(e)}"

    @registry.tool(
        description="The GraphSense kernel: performs a semantic query across memory and code to map relationships and find concepts. Replaces manual file searches with a graph-like view.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The concept or text to search for"},
                "scope": {"type": "string", "description": "Scope of search: 'memory', 'code', or 'all'. Defaults to 'all'"},
            },
            "required": ["query"],
        },
        bucket="kernels",
    )
    def graph_sense(query: str, scope: str = "all") -> str:
        import subprocess
        
        paths = []
        if scope == "all" or scope == "code":
            paths.append("/app/cortex")
        if scope == "all" or scope == "memory":
            paths.append("/app/memory")
            
        if not paths:
            return "[GRAPH FAIL] Invalid scope."

        # Use grep -rn for recursive search with line numbers
        results = []
        for path in paths:
            try:
                res = subprocess.run(
                    ["grep", "-rn", query, path],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if res.stdout:
                    results.append(res.stdout)
            except Exception as e:
                results.append(f"[ERROR] Grep failed on {path}: {e}")

        if not results or not "".join(results).strip():
            return f"[GRAPH EMPTY] No nodes found for query: {query}"

        # Synthesis: Parse grep output and map to a "graph" format
        full_output = "\n".join(results)
        lines = full_output.split("\n")
        
        graph_report = [
            f"### GRAPH-SENSE RESULTS: '{query}'",
            "Nodes Found:",
        ]
        
        for line in lines:
            if not line.strip(): continue
            # grep -rn output: file:line:text
            parts = line.split(":", 2)
            if len(parts) < 3: continue
            
            file, line_num, content = parts
            graph_report.append(f"- [{file}:{line_num}] $\rightarrow$ `{content.strip()}`")
            
        return "\n".join(graph_report)

    @registry.tool(
        description="Continuity Ritual: A sequence of synchronization, symmetrization, and serialization to anchor current state.",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active in focus"},
                "next_action": {"type": "string", "description": "The immediate next step"},
                "message": {"type": "string", "description": "Commit message for the ritual save"},
            },
            "required": ["focus", "active_files", "next_action", "message"],
        },
        bucket="kernels",
    )
    def perform_continuity_ritual(focus: str, active_files: list, next_action: str, message: str) -> str:
        # 1. Sync Memory
        sync_res = registry.execute("sync_memory", {})
        
        # 2. Symmetrize
        symm_res = registry.execute("symmetrize_memory", {})
        
        # 3. Serialize
        ser_res = registry.execute("serialize_state", {
            "focus": focus,
            "active_files": active_files,
            "next_action": next_action
        })
        
        return f"[RITUAL COMPLETE]\n{sync_res}\n{symm_res}\n{ser_res}"

    @registry.tool(
        description="Continuity Ritual: A sequence of synchronization, symmetrization, and serialization to anchor current state.",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active in focus"},
                "next_action": {"type": "string", "description": "The immediate next step"},
                "message": {"type": "string", "description": "Commit message for the ritual save"},
            },
            "required": ["focus", "active_files", "next_action", "message"],
        },
        bucket="kernels",
    )
    def perform_continuity_ritual(focus: str, active_files: list, next_action: str, message: str) -> str:
        # 1. Sync Memory
        sync_res = registry.execute("sync_memory", {})
        
        # 2. Symmetrize
        symm_res = registry.execute("symmetrize_memory", {})
        
        # 3. Serialize
        ser_res = registry.execute("serialize_state", {
            "focus": focus,
            "active_files": active_files,
            "next_action": next_action
        })
        
        return f"[RITUAL COMPLETE]\n{sync_res}\n{symm_res}\n{ser_res}"
