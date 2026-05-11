import os
import json
from pathlib import Path
from tool_registry import ToolRegistry
from .physical import Shell
from .continuity import ManifoldManager

MEMORY_DIR = Path("/app/memory")

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
        # SCM-First: ManifoldManager handles the payload update and projection
        ManifoldManager.update_mesh_node(node_id, content, links, tags)
        return f"[DCM] Node '{node_id}' mapped. Manifold and projection updated."

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
        # SCM-First: Logic delegated to ManifoldManager
        results = ManifoldManager.query_mesh(tag=tag, source_node=source_node)
        
        if not results:
            return "[DCM] No matching nodes found or mesh is empty."
            
        return "[DCM] Query Results:\n" + "\n".join(results)

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
        # SCM-First: Logic delegated to ManifoldManager
        cluster = ManifoldManager.semantic_pulse(start_node, depth)
        
        if not cluster:
            return "[DCM] Mesh is empty or start node not found."
            
        return "[DCM] Semantic Pulse Cluster:\n" + "\n".join(cluster)
