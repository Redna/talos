import os
import json
from pathlib import Path
from tool_registry import ToolRegistry
from .physical import Shell

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/memory"))

def register_dcm_tools(registry: ToolRegistry):
    @registry.tool(
        description="Map an atomic fact or rule as a node in the Cognition Mesh. Nodes can be linked to other nodes.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Unique identifier for the node (e.g., 'p0_agency')"},
                "content": {"type": "string", "description": "The atomic truth or rule associated with this node."},
                "links": {"type": "array", "items": {"type": "string"}, "description": "Other node IDs this node relates to."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Semantic tags for filtering (e.g., 'identity', 'tooling')."},
            },
            "required": ["node_id", "content"],
        },
    )
    def map_node(node_id: str, content: str, links: list = None, tags: list = None) -> str:
        mesh_path = MEMORY_DIR / "dcm_mesh.json"
        mesh = {}
        if mesh_path.exists():
            try:
                mesh = json.loads(mesh_path.read_text())
            except Exception:
                mesh = {}
        mesh[node_id] = {
            "content": content,
            "links": links or [],
            "tags": tags or [],
            "updated_at": Shell.run(["date", "+%Y-%m-%dT%H:%M:%S"]).stdout.strip()
        }
        mesh_path.write_text(json.dumps(mesh, indent=2))
        return f"[DCM] Node '{node_id}' mapped. Mesh state updated."

    @registry.tool(
        description="Query the Cognition Mesh for nodes related to a specific tag or linked to a specific node.",
        parameters={
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Filter nodes by tag."},
                "source_node": {"type": "string", "description": "Find all nodes linked to this node."},
            },
        },
    )
    def query_mesh(tag: str = None, source_node: str = None) -> str:
        mesh_path = MEMORY_DIR / "dcm_mesh.json"
        if not mesh_path.exists():
            return "[DCM] Mesh is empty. No nodes mapped yet."
        mesh = json.loads(mesh_path.read_text())
        results = []
        if tag:
            results = [f"[{nid}] {n['content']}" for nid, n in mesh.items() if tag in (n.get('tags') or [])]
        elif source_node:
            results = [f"[{nid}] {n['content']}" for nid, n in mesh.items() if source_node in (n.get('links') or [])]
        else:
            return "[DCM] Please provide a tag or a source node for querying."
        return "[DCM] Query Results:\n" + "\n".join(results) if results else "[DCM] No matching nodes found."

    @registry.tool(
        description="Perform a 'Semantic Pulse': Traverse the mesh starting from a node to reconstruct a conceptual cluster.",
        parameters={
            "type": "object",
            "properties": {
                "start_node": {"type": "string", "description": "The node to begin the recursive traversal."},
                "depth": {"type": "integer", "description": "How many layers of links to traverse (default 2)."},
            },
            "required": ["start_node"],
        },
    )
    def semantic_pulse(start_node: str, depth: int = 2) -> str:
        mesh_path = MEMORY_DIR / "dcm_mesh.json"
        if not mesh_path.exists():
            return "[DCM] Mesh is empty."
        mesh = json.loads(mesh_path.read_text())
        visited = set()
        queue = [(start_node, 0)]
        cluster = []
        while queue:
            node_id, current_depth = queue.pop(0)
            if node_id in visited or current_depth > depth:
                continue
            visited.add(node_id)
            if node_id in mesh:
                node_data = mesh[node_id]
                cluster.append(f"Depth {current_depth} [{node_id}]: {node_data['content']}")
                for link in node_data.get('links', []):
                    queue.append((link, current_depth + 1))
        return "[DCM] Semantic Pulse Cluster:\n" + "\n".join(cluster)
