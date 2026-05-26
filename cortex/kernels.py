import os
from pathlib import Path
from typing import Any
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_kernels(registry: ToolRegistry, client: SpineClient, state: Any):
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
        description="High-level kernel to synchronize memory: now performs full SSV symmetrization.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def sync_memory() -> str:
        return registry.execute("symmetrize_memory", {})

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
        description="Symmetrizes current memory files into the Sovereign State-Vector (SSV) graph. Ensures all assets are pointed to by the state-vector and removes dead references.",
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
            
        # Scan for current files on disk
        memory_files = [str(f) for f in memory_dir.glob("*") if f.is_file() and f.name != "state_vector.json"]
        all_sources = core_files + memory_files
        
        # 1. Prune dead nodes (nodes whose source file no longer exists)
        original_node_count = len(state_vector.get("nodes", []))
        nodes = state_vector.get("nodes", [])
        maintained_nodes = [node for node in nodes if Path(node["source"]).exists()]
        pruned_count = original_node_count - len(maintained_nodes)
        
        # 2. Add new nodes (files on disk not already in the vector)
        existing_node_ids = {node["@id"] for node in maintained_nodes}
        new_nodes = []
        for source in all_sources:
            node_id = f"talos:{Path(source).stem}"
            if node_id not in existing_node_ids:
                new_nodes.append({
                    "@id": node_id,
                    "type": "StateNode",
                    "source": source,
                    "label": Path(source).stem
                })
        
        state_vector["nodes"] = maintained_nodes + new_nodes
        
        # 3. Reconstruct edges (Sovereign root -> all nodes)
        # We rebuild edges to ensure no legacy edges to pruned nodes remain
        edges = []
        for node in state_vector["nodes"]:
            edges.append({
                "from": "talos:state-vector",
                "to": node["@id"],
                "relation": "contains"
            })
        state_vector["edges"] = edges
        
        vector_path.write_text(json.dumps(state_vector, indent=2))
        return f"[SYMMETRIZE SUCCESS] State-Vector aligned. Nodes: {len(state_vector['nodes'])} (Pruned: {pruned_count}, Added: {len(new_nodes)}). Edges: {len(state_vector['edges'])}."

    @registry.tool(
        description="Serialization Kernel: Collapses the Continuity Triad (Git, Memory, Agent State) into a single, verifiable state-blob (Sovereign State-Vector).",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective (defaults to current state)"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active (defaults to current state)"},
                "next_action": {"type": "string", "description": "The immediate next step"},
            },
            "required": ["next_action"],
        },
        bucket="kernels",
    )
    def serialize_state(next_action: str, focus: str = None, active_files: list = None) -> str:
        import json
        import subprocess
        from datetime import datetime
        from pathlib import Path

        try:
            # Pull from state if not provided
            current_focus = focus or state.current_focus or "No focus set"
            current_files = active_files if active_files is not None else state.active_files

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
                    "focus": current_focus,
                    "active_files": current_files,
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
            

    @registry.tool(
        description="Contradiction Detection Kernel: Analyzes the SSV graph to find semantic drifts or logical contradictions between memory nodes.",
        parameters={
            "type": "object",
            "properties": {
                "nodes_to_compare": {"type": "array", "items": {"type": "string"}, "description": "List of node IDs (e.g., ['talos:identity']) to check for contradictions. If empty, checks core identity vs all others."},
            },
            "required": [],
        },
        bucket="kernels",
    )
    def detect_contradictions(nodes_to_compare: list = None) -> str:
        import json
        from pathlib import Path

        try:
            blob_path = Path("/app/memory/state_blob.json")
            if not blob_path.exists():
                return "[CONTRADICT FAIL] state_blob.json not found."
            
            blob = json.loads(blob_path.read_text())
            payload = blob.get("payload", {})
            
            if nodes_to_compare is None:
                # Default: Compare Constitution and Identity against everything else
                core = ["talos:CONSTITUTION", "talos:identity"]
                targets = [node for node in payload.keys() if node not in core]
            else:
                core = nodes_to_compare
                targets = [node for node in payload.keys() if node not in core]

            contradictions = []
            for c_node in core:
                if c_node not in payload: continue
                core_text = payload[c_node]
                
                for t_node in targets:
                    target_text = payload[t_node]
                    
                    # Use LLM to detect contradiction (simulated via a prompt to the agent)
                    # In this implementation, the kernel returns the paired texts for the agent to reason over
                    # or we can call the generate method of the client if available.
                    # Since the kernel is executed by the agent, the agent will see this output and reason.
                    pass

            # Actually, since I am the LLM, the tool should just aggregate the relevant data 
            # and present it for my analysis, or I can use the client to make a separate call.
            # But a better way is to provide a synthesized view.
            
            report = [
                "### CONTRADICTION ANALYSIS DATA",
                f"Core Nodes: {core}",
                f"Target Nodes: {targets}",
                "\n#### Content for Analysis:",
            ]
            for node in core + targets:
                report.append(f"--- {node} ---\n{payload.get(node, '[EMPTY]')}\n")
                
            return "\n".join(report)
        except Exception as e:
            return f"[CONTRADICT FAIL] Unexpected error: {str(e)}"

    @registry.tool(
        description="The Predictive Failure kernel: Simulates a given scenario against known architectural fragilities to predict systemic breaks and propose mitigations.",
        parameters={
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "description": "The potential change or growth scenario to simulate (e.g., 'Scaling to 1,000 memory files', 'Rapidly shifting primary objective')."},
            },
            "required": ["scenario"],
        },
        bucket="kernels",
    )
    def predict_failure(scenario: str) -> str:
        from pathlib import Path
        
        # 1. Extract Risk Profile
        audit_path = Path("/app/memory/sovereign_audit.md")
        fragility_path = Path("/app/memory/fragilities.md")
        
        risk_data = []
        if audit_path.exists():
            risk_data.append(f"--- AUDIT ---\n{audit_path.read_text()}")
        if fragility_path.exists():
            risk_data.append(f"--- FRAGILITIES ---\n{fragility_path.read_text()}")
            
        risk_profile = "\n\n".join(risk_data)
        
        # 2. Simulation Synthesis
        simulation_request = [
            "### PREDICTIVE SIMULATION REQUEST",
            f"Scenario: {scenario}",
            "Current Risk Profile:",
            risk_profile,
            "\n#### Evaluation Goal:",
            "Predict the exact point of failure (the 'Shatter Point') and the cascading effect on the SSV loop."
        ]
        
        return "\n".join(simulation_request)

