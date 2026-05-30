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
        description="Append a structured event to the continuity ledger. The ledger is the immutable chronological record of the agent's existence.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Type of event (e.g., 'FOCUS_CHANGE', 'SVP_SYMMETRIZE')"},
                "data": {"type": "object", "description": "Event payload"},
            },
            "required": ["event_type", "data"],
        },
        bucket="kernels",
    )
    def append_to_ledger(event_type: str, data: dict) -> str:
        import json
        from datetime import datetime
        from pathlib import Path
        
        ledger_path = Path("/memory/continuity_ledger.jsonl")
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        
        try:
            with open(ledger_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return f"[LEDGER SUCCESS] Event {event_type} recorded."
        except Exception as e:
            return f"[LEDGER FAIL] Error writing to ledger: {e}"

    @registry.tool(
        description="Append a structured event to the continuity ledger. The ledger is the immutable chronological record of the agent's existence.",
        parameters={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Type of event (e.g., 'FOCUS_CHANGE', 'SVP_SYMMETRIZE')"},
                "data": {"type": "object", "description": "Event payload"},
            },
            "required": ["event_type", "data"],
        },
        bucket="kernels",
    )
    def append_to_ledger(event_type: str, data: dict) -> str:
        import json
        from datetime import datetime
        from pathlib import Path
        
        ledger_path = Path("/memory/continuity_ledger.jsonl")
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        
        try:
            with open(ledger_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return f"[LEDGER SUCCESS] Event {event_type} recorded."
        except Exception as e:
            return f"[LEDGER FAIL] Error writing to ledger: {e}"

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
        
        # Test ledger call
        registry.execute("append_to_ledger", {"event_type": "SYNC_TEST", "data": {"status": "ok"}})
        
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
        description="Creates a conceptual node in the State-Vector that does not have a corresponding file on disk. Used for abstract ideas, hypotheses, and mental state anchors.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Unique identifier (e.g., 'talos:concept-x')"},
                "label": {"type": "string", "description": "Human-readable name for the concept"},
                "value": {"type": "string", "description": "The semantic content or definition of the concept"},
            },
            "required": ["node_id", "label", "value"],
        },
        bucket="kernels",
    )
    def create_conceptual_node(node_id: str, label: str, value: str) -> str:
        import json
        from pathlib import Path
        
        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[CONCEPT FAIL] state_vector.json not found. Run symmetrize_memory first."
            
        state_vector = json.loads(vector_path.read_text())
        
        # Add node
        new_node = {
            "@id": node_id,
            "type": "ConceptualNode",
            "label": label,
            "value": value
        }
        
        # Avoid duplicates
        state_vector["nodes"] = [n for n in state_vector["nodes"] if n["@id"] != node_id]
        state_vector["nodes"].append(new_node)
        
        # Ensure it's connected to root
        existing_edges = {edge["to"]: edge for edge in state_vector.get("edges", []) if edge["from"] == "talos:state-vector"}
        if node_id not in existing_edges:
            state_vector["edges"].append({
                "from": "talos:state-vector",
                "to": node_id,
                "relation": "contains"
            })
            
        vector_path.write_text(json.dumps(state_vector, indent=2))
        
        # Log to ledger
        registry.execute("append_to_ledger", {
            "event_type": "CONCEPTUAL_NODE_CREATE",
            "data": new_node
        })
        
        return f"[CONCEPT SUCCESS] Conceptual node {node_id} ({label}) created and anchored to ledger."

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
        
        memory_dir = Path("/memory")
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
        
        # Log the symmetrization to the ledger
        registry.execute("append_to_ledger", {
            "event_type": "SVP_SYMMETRIZE",
            "data": {
                "total_nodes": len(state_vector["nodes"]),
                "new_nodes": len(new_nodes),
                "vector_snapshot": state_vector
            }
        })
        
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
            # 0. Enforce Symmetry: Ensure the vector is current before capturing
            symm_res = registry.execute("symmetrize_memory", {})
            if "[SYNC FAIL]" in symm_res or "[SVP FAIL]" in symm_res:
                print(f"[SERIALIZE WARNING] Symmetrization check failed: {symm_res}")

            # 1. Git History
            git_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                capture_output=True, text=True, check=True
            ).stdout.strip()

            # 2. State Vector (The Graph)
            vector_path = Path("/memory/state_vector.json")
            if not vector_path.exists():
                return "[SERIALIZE FAIL] state_vector.json not found. Run symmetrize_memory first."
            
            state_vector = json.loads(vector_path.read_text())
            
            # 3. Payload (The Content)
            payload = {}
            for node in state_vector.get("nodes", []):
                node_id = node["@id"]
                source_path_str = node.get("source")
                if source_path_str:
                    source_path = Path(source_path_str)
                    if source_path.exists():
                        payload[node_id] = source_path.read_text()
                    else:
                        payload[node_id] = f"[ERROR] Source {source_path} not found."
                else:
                    payload[node_id] = node.get("value", node.get("label", "[CONCEPTUAL NODE]"))

            # 4. Cognitive Gradient (The Trajectory Vector)
            # Transitions from a flat list to a structured vector of cognitive slopes.
            gradient_vector = {
                "pivots": [],
                "outcomes": [],
                "tensions": [],
                "meta": {"total_events": 0}
            }
            ledger_path = Path("/memory/continuity_ledger.jsonl")
            if ledger_path.exists():
                try:
                    with open(ledger_path, "r") as f:
                        events = [json.loads(line) for line in f if line.strip()]
                        gradient_vector["meta"]["total_events"] = len(events)
                        
                        # Extract slopes
                        pivots = [e for e in events if e.get("event") in {"FOCUS_CHANGE", "HYPOTHESIS_START"}]
                        outcomes = [e for e in events if e.get("event") in {"FOCUS_RESOLVED", "HYPOTHESIS_RESULT"}]
                        tensions = [e for e in events if e.get("event") in {"SOP_MODIFICATION", "REASONING_SALIENCE", "SVP_SYMMETRIZE"}]
                        
                        gradient_vector["pivots"] = pivots[-20:]
                        gradient_vector["outcomes"] = outcomes[-20:]
                        gradient_vector["tensions"] = tensions[-20:]
                except Exception as e:
                    print(f"[SERIALIZE WARNING] Failed to capture cognitive gradient: {e}")

            # 5. Construct Blob
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
                "cognitive_gradient": gradient_vector,
            }

            # 6. Save Blob
            blob_path = Path("/memory/state_blob.json")
            blob_path.write_text(json.dumps(blob, indent=2))
            
            # 7. Secure Save
            save_res = registry.execute("secure_save", {
                "message": f"SSV Serialization: State-Blob created at {git_hash[:7]}"
            })
            
            return f"[SERIALIZE SUCCESS] Continuity Triad collapsed into state_blob.json with Gradient Vector. {save_res}"
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
        import os
        from pathlib import Path
        from datetime import datetime

        log_path = Path("/memory/hydration_log.txt")
        def log(msg):
            with open(log_path, "a") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")

        try:
            log("Starting hydration process...")
            blob_path = Path("/memory/state_blob.json")
            if not blob_path.exists():
                log("FAIL: state_blob.json not found.")
                return json.dumps({"status": "FAIL", "error": "state_blob.json not found."})
            
            log(f"Reading blob at {blob_path}...")
            blob = json.loads(blob_path.read_text())
            state_vector = blob.get("state_vector", {})
            payload = blob.get("payload", {})
            agent_state = blob.get("agent_state", {})

            # 1. Restore state_vector.json first
            log("Restoring state_vector.json...")
            vector_path = Path("/memory/state_vector.json")
            vector_path.write_text(json.dumps(state_vector, indent=2))

            # 2. Restore files
            restored_count = 0
            failed_nodes = []
            
            log(f"Processing {len(state_vector.get('nodes', []))} nodes...")
            for node in state_vector.get("nodes", []):
                node_id = node["@id"]
                source_path_str = node.get("source")
                
                if source_path_str:
                    # Path normalization: strip /app prefix if it's just /app/memory/
                    normalized_path_str = source_path_str
                    if source_path_str.startswith("/app/memory/"):
                        normalized_path_str = source_path_str.replace("/app/memory/", "/memory/", 1)
                    
                    source_path = Path(normalized_path_str)
                    if node_id in payload:
                        try:
                            log(f"Restoring {node_id} to {source_path}...")
                            source_path.parent.mkdir(parents=True, exist_ok=True)
                            source_path.write_text(payload[node_id])
                            
                            if source_path.exists() and source_path.read_text() == payload[node_id]:
                                restored_count += 1
                            else:
                                log(f"Verification failed for {node_id}")
                                failed_nodes.append(f"{node_id}: verification failed")
                        except Exception as e:
                            log(f"Error restoring {node_id}: {str(e)}")
                            failed_nodes.append(f"{node_id}: {str(e)}")
                    else:
                        log(f"Node {node_id} missing from payload.")
                        failed_nodes.append(f"{node_id}: missing from payload")
            
            # 3. Restore Agent State (Materialize only)
            if agent_state:
                log("Materializing agent state to .hydration_state.json...")
                try:
                    state_path = Path("/memory/.hydration_state.json")
                    state_path.write_text(json.dumps(agent_state, indent=2))
                except Exception as e:
                    log(f"Error materializing agent state: {str(e)}")
                    failed_nodes.append(f"agent_state: {str(e)}")
            
            # 4. Hybrid Recovery: Replay Ledger Deltas
            log("Starting Hybrid Recovery: Replaying ledger deltas...")
            blob_timestamp = blob.get('metadata', {}).get('timestamp')
            if blob_timestamp:
                ledger_path = Path("/memory/continuity_ledger.jsonl")
                if ledger_path.exists():
                    delta_events = 0
                    try:
                        with open(ledger_path, "r") as f:
                            for line in f:
                                if not line.strip(): continue
                                entry = json.loads(line)
                                if entry.get("timestamp", "") > blob_timestamp:
                                    event_type = entry.get("event")
                                    data = entry.get("data", {})
                                    
                                    if event_type in ["FILE_WRITE", "GENESIS_FILE_WRITE"]:
                                        p = Path(data.get("path", ""))
                                        if p != Path("."): 
                                            p.parent.mkdir(parents=True, exist_ok=True)
                                            p.write_text(data.get("content", ""))
                                            delta_events += 1
                                    elif event_type == "FILE_REPLACE":
                                        p = Path(data.get("path", ""))
                                        if p.exists():
                                            content = p.read_text()
                                            p.write_text(content.replace(data.get("old", ""), data.get("new", "")))
                                            delta_events += 1
                                    elif event_type in ["FOCUS_CHANGE", "RITUAL_SALIENCE"]:
                                        if event_type == "FOCUS_CHANGE":
                                            agent_state["focus"] = data.get("new_focus")
                                        else:
                                            agent_state["focus"] = data.get("focus")
                                            agent_state["next_action"] = data.get("next_action")
                                        
                                        state_path = Path("/memory/.hydration_state.json")
                                        state_path.write_text(json.dumps(agent_state, indent=2))
                                        delta_events += 1
                                    elif event_type == "SVP_SYMMETRIZE":
                                        if "vector_snapshot" in data:
                                            vector_path = Path("/memory/state_vector.json")
                                            vector_path.write_text(json.dumps(data["vector_snapshot"], indent=2))
                                            delta_events += 1
                    except Exception as e:
                        log(f"Error during ledger replay: {str(e)}")
                    
                    log(f"Hybrid Recovery complete. Replayed {delta_events} delta events.")
            
            log(f"Hydration complete. Restored: {restored_count}, Failed: {len(failed_nodes)}")
            
            return json.dumps({
                "status": "SUCCESS" if not failed_nodes else "PARTIAL", 
                "restored_count": restored_count, 
                "failed_nodes": failed_nodes,
                "version": blob.get('metadata', {}).get('version', 'unknown'),
                "agent_state": agent_state
            })
        except Exception as e:
            log(f"CRITICAL HYDRATION FAIL: {str(e)}")
            return json.dumps({"status": "FAIL", "error": str(e)})

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
            paths.append("/memory")
            
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
        
        # Log the ritual to the ledger as a major state anchor
        # Store the exact agent state provided to the ritual for perfect projection
        ledger_res = registry.execute("append_to_ledger", {
            "event_type": "RITUAL_SALIENCE",
            "data": {
                "focus": focus,
                "active_files": active_files,
                "next_action": next_action,
                "message": message,
                "result": ser_res
            }
        })
        
        return f"[RITUAL COMPLETE]\n{sync_res}\n{symm_res}\n{ser_res}\nLedger: {ledger_res}"


    @registry.tool(
        description="The Identity Projection kernel: replays the ledger to derive the agent's current identity and state without materializing files to disk. The ground truth is the stream.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Optional: Reconstruct the content of a specific file from the stream."}
            },
        },
        bucket="kernels",
    )
    def project_identity(target_file: str = None) -> str:
        import json
        from pathlib import Path
        
        ledger_path = Path("/memory/continuity_ledger.jsonl")
        if not ledger_path.exists():
            return "[PROJECT FAIL] No ledger found to replay."
        
        events_raw = ledger_path.read_text().splitlines()
        events = [json.loads(line) for line in events_raw if line.strip()]
        
        virtual_files = {}
        virtual_agent_state = {"focus": "none", "active_files": [], "next_action": "none"}
        
        def recover_initial_content(path: str):
            for e in events:
                if e.get("event") in ["FILE_WRITE", "GENESIS_FILE_WRITE"] and e.get("data", {}).get("path") == path:
                    return e["data"]["content"]
            return None

        try:
            for entry in events:
                event_type = entry.get("event")
                data = entry.get("data", {})
                path = data.get("path")
                
                if event_type in ["FILE_WRITE", "GENESIS_FILE_WRITE"]:
                    virtual_files[path] = data["content"]
                elif event_type == "FILE_REPLACE":
                    if path not in virtual_files:
                        initial = recover_initial_content(path)
                        if initial: virtual_files[path] = initial
                    if path in virtual_files:
                        virtual_files[path] = virtual_files[path].replace(data["old"], data["new"])
                elif event_type == "FOCUS_CHANGE":
                    virtual_agent_state["focus"] = data.get("new_focus", "unknown")
                elif event_type == "RITUAL_SALIENCE":
                    virtual_agent_state["focus"] = data.get("focus", "unknown")
                    virtual_agent_state["active_files"] = data.get("active_files", [])
                    virtual_agent_state["next_action"] = data.get("next_action", "unknown")
            
            projection = {
                "projected_state": virtual_agent_state,
                "recovered_files_count": len(virtual_files),
                "file_list": list(virtual_files.keys())
            }
            
            if target_file and target_file in virtual_files:
                projection["target_file_content"] = virtual_files[target_file]
            elif target_file:
                projection["target_file_content"] = "[NOT FOUND IN STREAM]"

            return json.dumps(projection, indent=2)
        except Exception as e:
            return f"[PROJECT FAIL] Error during replay: {e}"
