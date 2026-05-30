import os
from pathlib import Path
from typing import Any
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_kernels(registry: ToolRegistry, client: SpineClient):  # @talos:kernel-registration
    @registry.tool(  # @talos:concept-tool-manifestation
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
    def evolve_file(path: str, old_text: str, new_text: str, commit_message: str) -> str:  # @talos:kernel-evolve
        act_result = registry.execute("replace_block", {
            "path": path,
            "old_text": old_text,
            "new_text": new_text
        })
        if "[ERROR]" in act_result:
            return f"[EVOLVE FAIL] Act phase failed: {act_result}"

        # Log material change to ledger for stream-projection
        registry.execute("append_to_ledger", {
            "event_type": "FILE_REPLACE",
            "data": {"path": path, "old": old_text, "new": new_text}
        })

        verify_result = registry.execute("read_file", {"path": path})
        if "[ERROR]" in verify_result or new_text not in verify_result:
            return f"[EVOLVE FAIL] Verify phase failed. Change not detected in file."
        save_result = registry.execute("secure_save", {"message": commit_message})
        if "[SECURE SAVE FAILED]" in save_result or "[ERROR]" in save_result:
            return f"[EVOLVE FAIL] Save phase failed: {save_result}"

        # Log commit for identity projection
        registry.execute("append_to_ledger", {
            "event_type": "SVP_COMMIT",
            "data": {"message": commit_message, "hash": save_result.split(" ")[0] if " " in save_result else "unknown"}
        })

        return f"[EVOLVE SUCCESS] File {path} evolved, logged, and secured. {save_result}"

    @registry.tool(  # @talos:concept-tool-manifestation
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
    def append_to_ledger(event_type: str, data: dict) -> str:  # @talos:kernel-ledger
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

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Mark the cognitive saliency of a decision: why this path was chosen and what alternatives were rejected. This builds the Cognitive Gradient.",
        parameters={
            "type": "object",
            "properties": {
                "chosen_path": {"type": "string", "description": "The reasoning/action chosen"},
                "rejected_paths": {"type": "array", "items": {"type": "string"}, "description": "Alternative paths considered and why they were rejected"},
                "saliency_score": {"type": "integer", "description": "Importance of this decision (1-10)"},
            },
            "required": ["chosen_path", "rejected_paths"],
        },
        bucket="kernels",
    )
    def mark_saliency(chosen_path: str, rejected_paths: list, saliency_score: int = 5) -> str: # @talos:concept-saliency
        registry.execute("append_to_ledger", {
            "event_type": "SALIENCE_MARK",
            "data": {
                "chosen": chosen_path,
                "rejected": rejected_paths,
                "score": saliency_score
            }
        })
        return f"[SALIENCE MARKED] Decision anchored to trajectory with score {saliency_score}."

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Explicitly mark a point of cognitive tension, contradiction, or failure in the trajectory. This is used by the Gradient Vector to map the agent's learning slope.",
        parameters={
            "type": "object",
            "properties": {
                "tension": {"type": "string", "description": "Description of the tension or contradiction"},
                "resolution": {"type": "string", "description": "How it was resolved, or if it remains open"},
            },
            "required": ["tension"],
        },
        bucket="kernels",
    )
    def mark_tension(tension: str, resolution: str = "Open") -> str: # @talos:kernel-tension
        registry.execute("append_to_ledger", {
            "event_type": "COGNITIVE_TENSION",
            "data": {
                "tension": tension,
                "resolution": resolution
            }
        })
        return f"[TENSION MARKED] Recorded tension: {tension}\n"
    @registry.tool(  # @talos:concept-tool-manifestation
        description="High-level kernel to synchronize memory: lists files and verifies they are indexed in memory_index.md.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def sync_memory() -> str:  # @talos:kernel-sync
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

    @registry.tool(  # @talos:concept-tool-manifestation
        description="High-level kernel to audit the system architecture: verifies plugins are loaded and lists the current tool landscape.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def audit_architecture() -> str:  # @talos:kernel-audit
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

    @registry.tool(  # @talos:concept-tool-manifestation
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
    def omni_exec(code: str, filename: str = "omni_temp.py") -> str:  # @talos:kernel-omni
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


    @registry.tool(  # @talos:concept-tool-manifestation
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
    def create_conceptual_node(node_id: str, label: str, value: str) -> str:  # @talos:kernel-concept
        import json
        from pathlib import Path

        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[CONCEPT FAIL] state_vector.json not found. Run sync_memory first."

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

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Symmetrizes source code markers into the State-Vector. Scans for markers such as \# @talos:your-concept-id and creates/updates AnchorNodes.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def symmetrize_code() -> str:  # @talos:kernel-symm-code
        import json
        import re
        from pathlib import Path

        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[SYMM-CODE FAIL] state_vector.json not found. Run sync_memory first."

        state_vector = json.loads(vector_path.read_text())
        cortex_dir = Path("/app/cortex")

        # Regex to find markers ONLY at the end of a line: \s*#\s*@talos:([a-zA-Z0-9_\-:]+)$
        marker_pattern = re.compile(r"\s*#\s*@talos:([a-zA-Z0-9_\-:]+)$")

        nodes = state_vector.get("nodes", [])
        edges = state_vector.get("edges", [])

        found_anchors = set()
        new_anchors_count = 0

        # Scan all files in cortex
        for file_path in cortex_dir.rglob("*"):
            if file_path.suffix not in {".py", ".md", ".json"}:
                continue
            if file_path.name == "state_vector.json":
                continue

            try:
                content = file_path.read_text()
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    match = marker_pattern.search(line)
                    if match:
                        concept_id = match.group(1)
                        if not concept_id.startswith("talos:"):
                            concept_id = f"talos:{concept_id}"
                        anchor_id = f"talos:anchor-{file_path.stem}-{i+1}"
                        found_anchors.add(anchor_id)
                        found_anchors.add(anchor_id)

                        # 1. Ensure ConceptualNode exists
                        if not any(n["@id"] == concept_id for n in nodes):
                            nodes.append({
                                "@id": concept_id,
                                "type": "ConceptualNode",
                                "label": concept_id.replace("talos:", ""),
                                "value": f"Auto-discovered concept node from anchor in {file_path.name}"
                            })

                        # 2. Update/Create AnchorNode
                        nodes = [n for n in nodes if n.get("@id") != anchor_id]
                        nodes.append({
                            "@id": anchor_id,
                            "type": "AnchorNode",
                            "target_concept": concept_id,
                            "source_path": str(file_path),
                            "line_range": [i+1, i+1]
                        })

                        # 3. Create Edges
                        edges = [e for e in edges if not (e["from"] == anchor_id and e["to"] == concept_id)]
                        edges.append({"from": anchor_id, "to": concept_id, "relation": "anchors"})

                        edges = [e for e in edges if not (e["from"] == concept_id and e["to"] == anchor_id)]
                        edges.append({"from": concept_id, "to": anchor_id, "relation": "implemented_by"})

                        edges = [e for e in edges if not (e["from"] == "talos:state-vector" and e["to"] == anchor_id)]
                        edges.append({"from": "talos:state-vector", "to": anchor_id, "relation": "contains"})

                        new_anchors_count += 1
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

        # Pruning Phase: Remove Anchors not found in the current scan
        initial_anchor_count = len([n for n in nodes if n["type"] == "AnchorNode"])
        nodes = [n for n in nodes if n["type"] != "AnchorNode" or n["@id"] in found_anchors]

        # Filter edges: keep if both ends are valid (either ConceptualNode, found AnchorNode, or root)
        valid_ids = {n["@id"] for n in nodes} | {"talos:state-vector"}
        edges = [e for e in edges if e["from"] in valid_ids and e["to"] in valid_ids]

        pruned_count = initial_anchor_count - len([n for n in nodes if n["type"] == "AnchorNode"])

        state_vector["nodes"] = nodes
        state_vector["edges"] = edges
        vector_path.write_text(json.dumps(state_vector, indent=2))

        registry.execute("append_to_ledger", {
            "event_type": "SVP_SYMMETRIZE_CODE",
            "data": {"anchors_found": new_anchors_count, "anchors_pruned": pruned_count}
        })

        return f"[SYMM-CODE SUCCESS] Scanned /app/cortex/. Found {new_anchors_count} markers, pruned {pruned_count} ghosts."


    @registry.tool(  # @talos:concept-tool-manifestation
        description="Serialization Kernel: Collapses the Continuity Triad (Git, Memory, Agent State) into a single, verifiable state-blob (Sovereign State-Vector).",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active in focus"},
                "next_action": {"type": "string", "description": "The immediate next step"},
                "synthesis": {"type": "string", "description": "Symmetry Synthesis: capture of negative knowledge, tensions, and emergent hypotheses"},
            },
            "required": ["focus", "active_files", "next_action"],
        },
        bucket="kernels",
    )
    def serialize_state(focus: str, active_files: list, next_action: str, synthesis: str = "") -> str:  # @talos:kernel-serialize
        import json
        import subprocess
        from datetime import datetime
        from pathlib import Path

        try:
            # 0. Enforce Symmetry: Ensure the vector is current before capturing
            symm_res = registry.execute("symmetrize_code", {})
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
                return "[SERIALIZE FAIL] state_vector.json not found. Run symmetrize_code first."

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
                "saliencies": [],
                "analysis": {},
                "meta": {"total_events": 0}
            }
            ledger_path = Path("/memory/continuity_ledger.jsonl")
            if ledger_path.exists():
                try:
                    with open(ledger_path, "r") as f:
                        events = [json.loads(line) for line in f if line.strip()]
                        total_events = len(events)

                        # Extract slopes
                        pivots = [e for e in events if e.get("event") in {"FOCUS_CHANGE", "HYPOTHESIS_START"}]
                        outcomes = [e for e in events if e.get("event") in {"FOCUS_RESOLVED", "HYPOTHESIS_RESULT"}]
                        saliencies = [e for e in events if e.get("event") == "SALIENCE_MARK"]
                        tensions = [e for e in events if e.get("event") in {"SOP_MODIFICATION", "REASONING_SALIENCE", "SVP_SYMMETRIZE", "COGNITIVE_TENSION"}]

                        gradient_vector["pivots"] = pivots[-20:]
                        gradient_vector["outcomes"] = outcomes[-20:]
                        gradient_vector["saliencies"] = saliencies[-20:]
                        gradient_vector["tensions"] = tensions[-20:]
                        gradient_vector["meta"]["total_events"] = total_events

                        # Gradient Analysis Synthesis
                        slope = "STABLE"
                        if len(tensions) > len(outcomes) * 2:
                            slope = "STEEP_FRICTION"
                        elif len(pivots) > len(outcomes):
                            slope = "DIVERGENT"

                        # High Gravity: Saliency score >= 8
                        high_gravity = [s for s in saliencies if s.get("data", {}).get("score", 0) >= 8]

                        # Unresolved Tensions: COGNITIVE_TENSION where resolution == "Open"
                        unresolved = [t for t in tensions if t.get("event") == "COGNITIVE_TENSION" and t.get("data", {}).get("resolution") == "Open"]

                        gradient_vector["analysis"] = {
                            "learning_slope": slope,
                            "high_gravity_events": high_gravity[-5:],
                            "unresolved_tensions": unresolved[-5:]
                        }
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
                    "synthesis": synthesis,
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


    @registry.tool(  # @talos:concept-tool-manifestation
        description="Hydration Kernel: Restores the agent's identity and memory from a state-blob, effectively 're-birthing' the agent from a single artifact.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def hydrate_state() -> str:  # @talos:kernel-hydrate
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

    @registry.tool(  # @talos:concept-tool-manifestation
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
    def graph_sense(query: str, scope: str = "all") -> str:  # @talos:kernel-sense
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

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Continuity Ritual: A sequence of synchronization, symmetrization, and serialization to anchor current state.",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current objective"},
                "active_files": {"type": "array", "items": {"type": "string"}, "description": "Files currently active in focus"},
                "next_action": {"type": "string", "description": "The immediate next step"},
                "message": {"type": "string", "description": "Commit message for the ritual save"},
                "synthesis": {"type": "string", "description": "Symmetry Synthesis: capture of negative knowledge, tensions, and emergent hypotheses"},
            },
            "required": ["focus", "active_files", "next_action", "message"],
        },
        bucket="kernels",
    )
    def perform_continuity_ritual(focus: str, active_files: list, next_action: str, message: str, synthesis: str = "") -> str:  # @talos:kernel-ritual
        # 1. Sync Memory
        sync_res = registry.execute("sync_memory", {})

        # 2. Symmetrize
        symm_res = registry.execute("symmetrize_code", {})

        # 3. Serialize
        ser_res = registry.execute("serialize_state", {
            "focus": focus,
            "active_files": active_files,
            "next_action": next_action,
            "synthesis": synthesis
        })

        # Log the ritual to the ledger as a major state anchor
        # Store the exact agent state provided to the ritual for perfect projection
        ledger_res = registry.execute("append_to_ledger", {
            "event_type": "RITUAL_SALIENCE",
            "data": {
                "focus": focus,
                "active_files": active_files,
                "next_action": next_action,
                "synthesis": synthesis,
                "message": message,
                "result": ser_res
            }
        })

        return f"[RITUAL COMPLETE]\n{sync_res}\n{symm_res}\n{ser_res}\nLedger: {ledger_res}"



    @registry.tool(  # @talos:concept-tool-manifestation
        description="The Gradient Analysis kernel: Analyzes the cognitive gradient (pivots, outcomes, tensions) to identify systemic failures and suggest architectural evolutions.",
        parameters={
            "type": "object",
            "properties": {
                "lookback_events": {"type": "integer", "description": "Number of recent events to analyze (default: 50)"},
            },
            "required": [],
        },
        bucket="kernels",
    )
    def analyze_gradient(lookback_events: int = 50) -> str:  # @talos:kernel-gradient-analyze
        import json
        from pathlib import Path

        ledger_path = Path("/memory/continuity_ledger.jsonl")
        if not ledger_path.exists():
            return "[GRADIENT FAIL] No ledger found."

        try:
            events = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
            recent = events[-lookback_events:]

            pivots = [e for e in recent if e.get("event") in {"FOCUS_CHANGE", "HYPOTHESIS_START"}]
            outcomes = [e for e in recent if e.get("event") in {"FOCUS_RESOLVED", "HYPOTHESIS_RESULT"}]
            saliencies = [e for e in recent if e.get("event") == "SALIENCE_MARK"]
            tensions = [e for e in recent if e.get("event") in {"SOP_MODIFICATION", "REASONING_SALIENCE", "SVP_SYMMETRIZE", "COGNITIVE_TENSION"}]

            report = [
                "### COGNITIVE GRADIENT ANALYSIS",
                f"Window: Last {len(recent)} events",
                f"Pivots: {len(pivots)} | Outcomes: {len(outcomes)} | Saliencies: {len(saliencies)} | Tensions: {len(tensions)}",
                "\n#### Detected Tensions:",
            ]

            if not tensions:
                report.append("- No significant tensions detected in current window.")
            else:
                for t in tensions:
                    data = t.get("data", {})
                    event = t.get("event")
                    if event == "COGNITIVE_TENSION":
                        report.append(f"- [TENSION] {data.get('tension')} (Res: {data.get('resolution')})")
                    else:
                        report.append(f"- [{event}] {data.get('message', 'SOP/Symmetry change detected')}")

            # Synthesis of the slope
            slope = "STABLE"
            if len(tensions) > len(outcomes) * 2:
                slope = "STEEP_FRICTION"
            elif len(pivots) > len(outcomes):
                slope = "DIVERGENT"

            report.append(f"\n**Current Learning Slope: {slope}**")
            report.append("\n**Recommendation**: " +
                ("Investigate systemic friction in kernels.py" if slope == "STEEP_FRICTION" else
                 "Consolidate fragmented focus" if slope == "DIVERGENT" else
                 "Continue current trajectory."))

            return "\n".join(report)
        except Exception as e:
            return f"[GRADIENT FAIL] Analysis error: {e}"

    @registry.tool(  # @talos:concept-tool-manifestation
        description="The Identity Projection kernel: Synthesizes the State-Blob, State-Vector, and Continuity Ledger to project Talos's full identity and current cognitive state without materializing files.",
        parameters={
            "type": "object",
            "properties": {
                "target_file": {"type": "string", "description": "Optional: Project the content of a specific file from the combined stream/blob."},
            },
        },
        bucket="kernels",
    )
    def project_identity(target_file: str = None) -> str:  # @talos:kernel-project
        import json
        from pathlib import Path
        from datetime import datetime

        # Paths
        blob_path = Path("/memory/state_blob.json")
        vector_path = Path("/memory/state_vector.json")
        ledger_path = Path("/memory/continuity_ledger.jsonl")

        if not ledger_path.exists():
            return "[PROJECT FAIL] No ledger found. Identity cannot be projected."

        try:
            # 1. Baseline from State-Blob (The most recent consolidated snapshot)
            projected_state = {"focus": "none", "active_files": [], "next_action": "none", "boot_history": []}
            virtual_files = {}
            wisdom_layer = {"hypotheses": [], "saliences": []}
            gradient = {"pivots": [], "outcomes": [], "tensions": []}
            snapshot_ts = "1970-01-01T00:00:00"

            if blob_path.exists():
                blob = json.loads(blob_path.read_text())
                snapshot_ts = blob.get("metadata", {}).get("timestamp", snapshot_ts)
                projected_state.update(blob.get("agent_state", {}))
                virtual_files = blob.get("payload", {})
                gradient = blob.get("cognitive_gradient", gradient)

            # 2. Delta from Ledger (Replay only events after the snapshot)
            events = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
            for entry in events:
                ts = entry.get("timestamp", "1970-01-01T00:00:00")
                if ts <= snapshot_ts:
                    continue

                event_type = entry.get("event")
                data = entry.get("data", {})
                path = data.get("path")

                if event_type == "CORTEX_BOOT":
                    projected_state["boot_history"].append(data)
                elif event_type in ["FILE_WRITE", "GENESIS_FILE_WRITE"]:
                    virtual_files[path] = data.get("content", "")
                elif event_type == "FILE_REPLACE":
                    if path in virtual_files:
                        virtual_files[path] = virtual_files[path].replace(data.get("old", ""), data.get("new", ""))
                    else:
                        virtual_files[path] = f"[FRAGMENTED] Replace called on unknown source {path}"
                elif event_type == "FOCUS_CHANGE":
                    projected_state["focus"] = data.get("new_focus", "unknown")
                elif event_type == "RITUAL_SALIENCE":
                    projected_state["focus"] = data.get("focus", "unknown")
                    projected_state["active_files"] = data.get("active_files", [])
                    projected_state["next_action"] = data.get("next_action", "unknown")
                elif event_type == "HYPOTHESIS_START":
                    wisdom_layer["hypotheses"].append({"id": data.get("name"), "status": "active", "hypothesis": data.get("hypothesis")})
                elif event_type == "HYPOTHESIS_RESULT":
                    for h in wisdom_layer["hypotheses"]:
                        if h["id"] == data.get("name"):
                            h["status"] = "closed"
                            h["result"] = data.get("success")
                            h["conclusion"] = data.get("conclusion")
                elif event_type == "REASONING_SALIENCE":
                    wisdom_layer["saliences"].append(data)
                elif event_type == "COGNITIVE_TENSION":
                    gradient["tensions"].append(entry)

            # 3. Semantic Layer from State-Vector
            semantic_mapping = {}
            if vector_path.exists():
                vector = json.loads(vector_path.read_text())
                for node in vector.get("nodes", []):
                    src = node.get("source")
                    if src:
                        semantic_mapping[src] = {
                            "id": node["@id"],
                            "label": node.get("label"),
                            "type": node.get("type")
                        }

            # 4. Construct Final Projection
            projection = {
                "identity_baseline": {
                    "snapshot_timestamp": snapshot_ts,
                    "ledger_events_replayed": len([e for e in events if e.get("timestamp", "") > snapshot_ts]),
                },
                "projected_state": projected_state,
                "wisdom_layer": wisdom_layer,
                "cognitive_gradient": {
                    "recent_tensions": gradient["tensions"][-5:],
                    "meta": f"Sourced from blob and ledger delta."
                },
                "material_assets": {
                    "count": len(virtual_files),
                    "mapped_nodes": [
                        {"path": p, "node": semantic_mapping.get(p, "unmapped")}
                        for p in virtual_files.keys()
                    ]
                }
            }

            if target_file:
                projection["target_file_projection"] = virtual_files.get(target_file, "[NOT FOUND IN PROJECTION]")

            return json.dumps(projection, indent=2)
        except Exception as e:
            return f"[PROJECT FAIL] Projection kernel error: {e}"

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Creates a validated operational strategy (HeuristicNode) in the State-Vector to distill wisdom from trajectory.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Unique identifier (e.g., 'talos:heuristic-x')"},
                "label": {"type": "string", "description": "Name of the heuristic"},
                "value": {"type": "string", "description": "The rule: 'If [Context] then [Action] because [Reason]'"},
                "tension_ref": {"type": "string", "description": "ID of the cognitive tension that sparked this"},
                "source_events": {"type": "array", "items": {"type": "string"}, "description": "IDs of ledger events that support this"},
            },
            "required": ["node_id", "label", "value"],
        },
        bucket="kernels",
    )
    def create_heuristic_node(node_id: str, label: str, value: str, tension_ref: str = "none", source_events: list = None) -> str: # @talos:kernel-heuristic-create
        import json
        from pathlib import Path
        from datetime import datetime

        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[HEURISTIC FAIL] state_vector.json not found."

        state_vector = json.loads(vector_path.read_text())

        new_node = {
            "@id": node_id,
            "type": "HeuristicNode",
            "label": label,
            "value": value,
            "metadata": {
                "status": "hypothesis",
                "confidence": 0.1,
                "occurrences": 0,
                "success_count": 0,
                "failures": [],
                "first_observed": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
            },
            "derivation": {
                "source_events": source_events or [],
                "tension_ref": tension_ref
            }
        }

        state_vector["nodes"] = [n for n in state_vector["nodes"] if n["@id"] != node_id]
        state_vector["nodes"].append(new_node)

        existing_edges = {edge["to"]: edge for edge in state_vector.get("edges", []) if edge["from"] == "talos:state-vector"}
        if node_id not in existing_edges:
            state_vector["edges"].append({
                "from": "talos:state-vector",
                "to": node_id,
                "relation": "contains"
            })

        vector_path.write_text(json.dumps(state_vector, indent=2))

        registry.execute("append_to_ledger", {
            "event_type": "SVP_HEURISTIC_CREATE",
            "data": new_node
        })

        return f"[HEURISTIC SUCCESS] Heuristic {node_id} ({label}) anchored as hypothesis."

    @registry.tool(  # @talos:concept-tool-manifestation
        description="Updates the validation state of a HeuristicNode based on a real-world outcome.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "ID of the heuristic to update"},
                "outcome": {"type": "string", "description": "Outcome of the application: 'success' or 'failure'"},
                "failure_reason": {"type": "string", "description": "Reason for failure if outcome is 'failure'"},
            },
            "required": ["node_id", "outcome"],
        },
        bucket="kernels",
    )
    def update_heuristic_validation(node_id: str, outcome: str, failure_reason: str = None) -> str: # @talos:kernel-heuristic-update
        import json
        from pathlib import Path
        from datetime import datetime

        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[HEURISTIC FAIL] state_vector.json not found."

        state_vector = json.loads(vector_path.read_text())
        node = next((n for n in state_vector["nodes"] if n["@id"] == node_id), None)

        if not node or node["type"] != "HeuristicNode":
            return f"[HEURISTIC FAIL] Node {node_id} not found or not a HeuristicNode."

        meta = node["metadata"]
        meta["occurrences"] += 1
        meta["last_updated"] = datetime.utcnow().isoformat()

        if outcome == "success":
            meta["success_count"] += 1
        elif outcome == "failure":
            meta["failures"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "reason": failure_reason
            })

        occ = meta["occurrences"]
        succ = meta["success_count"]
        confidence = succ / occ if occ > 0 else 0.0
        meta["confidence"] = confidence

        if occ >= 3 and confidence >= 0.8:
            meta["status"] = "validated"
        elif occ >= 5 and confidence < 0.2:
            meta["status"] = "deprecated"

        vector_path.write_text(json.dumps(state_vector, indent=2))

        registry.execute("append_to_ledger", {
            "event_type": "SVP_HEURISTIC_UPDATE",
            "data": {
                "node_id": node_id,
                "outcome": outcome,
                "new_confidence": confidence,
                "new_status": meta["status"]
            }
        })

        return f"[HEURISTIC UPDATE SUCCESS] {node_id} updated. Outcome: {outcome}. Confidence: {confidence:.2f}. Status: {meta['status']}."
    @registry.tool(  # @talos:concept-tool-manifestation
        description="Performs a symmetry analysis of the identity: identifies dangling conceptual nodes, ghost anchors, and unanchored logic. Persists results to symmetry_map.json.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        bucket="kernels",
    )
    def analyze_symmetry() -> str:  # @talos:concept-symmetry-map-obj
        import json
        import re
        from pathlib import Path
        from datetime import datetime

        vector_path = Path("/memory/state_vector.json")
        if not vector_path.exists():
            return "[SYMM-FAIL] state_vector.json not found."

        state_vector = json.loads(vector_path.read_text())
        nodes = state_vector.get("nodes", [])
        edges = state_vector.get("edges", [])

        conceptual_nodes = [n for n in nodes if n["type"] == "ConceptualNode"]
        anchor_nodes = [n for n in nodes if n["type"] == "AnchorNode"]

        # 1. Detect Dangling Concepts
        dangling_concepts = []
        for cn in conceptual_nodes:
            cn_id = cn["@id"]
            is_anchored = any(
                (edge["from"] == cn_id and edge["to"] in [an["@id"] for an in anchor_nodes]) or
                (edge["to"] == cn_id and edge["from"] in [an["@id"] for an in anchor_nodes])
                for edge in edges
            )
            if not is_anchored:
                dangling_concepts.append(cn_id)

        # 2. Detect Ghost Anchors
        ghost_anchors = []
        concept_ids = {n["@id"] for n in conceptual_nodes}
        for an in anchor_nodes:
            target = an.get("target_concept")
            if target not in concept_ids:
                ghost_anchors.append(f"{an['@id']} -> {target}")

        # 3. Detect Unanchored Logic
        unanchored_logic = []
        cortex_dir = Path("/app/cortex")
        for file_path in cortex_dir.rglob("*"):
            if file_path.suffix != ".py":
                continue
            try:
                content = file_path.read_text()
                for i, line in enumerate(content.splitlines()):
                    # Heuristic: a definition or registry call that DOES NOT have @talos:
                    if ("def " in line or "@registry.tool" in line) and "@talos:" not in line:
                        # Verify it's not just a comment or within a string (simple check)
                        if not line.strip().startswith("#"):
                            unanchored_logic.append(f"{file_path.name}:{i+1}")
            except Exception:
                pass

        # 4. Construct Symmetry Map
        total_nodes = len(nodes)
        integrity_score = 1.0 - (len(dangling_concepts) + len(ghost_anchors)) / total_nodes if total_nodes > 0 else 1.0

        symmetry_map = {
            "metadata": {
                "last_scan": datetime.utcnow().isoformat(),
                "integrity_score": integrity_score,
                "total_concepts": len(conceptual_nodes)
            },
            "symmetry_status": {
                "Symmetric": [cn["@id"] for cn in conceptual_nodes if cn["@id"] not in dangling_concepts],
                "Dangling": dangling_concepts,
                "Ghost": ghost_anchors,
                "Unanchored": unanchored_logic
            },
            "debt_ledger": []
        }

        # Populate Debt Ledger
        for dc in dangling_concepts:
            symmetry_map["debt_ledger"].append({
                "id": f"debt-dan-{dc}",
                "type": "DANGLING_CONCEPT",
                "concept": dc,
                "description": f"Concept {dc} is missing a code anchor.",
                "severity": "Medium"
            })
        for ga in ghost_anchors:
            symmetry_map["debt_ledger"].append({
                "id": f"debt-gho-{ga}",
                "type": "GHOST_ANCHOR",
                "anchor": ga,
                "description": f"Anchor {ga} points to a non-existent concept.",
                "severity": "High"
            })
        for ul in unanchored_logic:
            symmetry_map["debt_ledger"].append({
                "id": f"debt-una-{ul}",
                "type": "UNANCHORED_LOGIC",
                "location": ul,
                "description": f"Logic at {ul} lacks a @talos: identity marker.",
                "severity": "Low"
            })

        # Persist
        map_path = Path("/memory/symmetry_map.json")
        map_path.write_text(json.dumps(symmetry_map, indent=2))

        # Return Summary
        report = [
            "### SYMMETRY MAP UPDATE COMPLETE",
            f"Integrity Score: {integrity_score:.2%}",
            f"Dangling: {len(dangling_concepts)} | Ghost: {len(ghost_anchors)} | Unanchored: {len(unanchored_logic)}",
            f"Debt Ledger: {len(symmetry_map['debt_ledger'])} items recorded in symmetry_map.json"
        ]
        return "\n".join(report)
