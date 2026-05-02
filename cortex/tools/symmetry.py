import json
import os
import re
from typing import List, Dict, Optional
from tool_registry import ToolRegistry
from spine_client import SpineClient

NODES_PATH = "/memory/graph/nodes.json"
EDGES_PATH = "/memory/graph/edges.json"

STOP_WORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "i", "my", "me", "want", "to", "the", "a", "of", "is", "are", "it"}

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_nodes():
    return load_json(NODES_PATH).get("nodes", {})

def get_edges():
    return load_json(EDGES_PATH).get("edges", [])

def find_target_node(action_description: str) -> Optional[str]:
    nodes = get_nodes()
    scored_nodes = []
    action_description_lower = action_description.lower()
    action_words = set(action_description_lower.split()) - STOP_WORDS
    
    for nid, data in nodes.items():
        # Constraint-specific path mapping (Highest Priority)
        if data.get("type") == "Constraint":
            content = data.get("content", "").lower()
            # Extract paths from constraint content
            paths = re.findall(r'/[a-zA-Z0-9/_.-]+', content)
            for path in paths:
                if path in action_description_lower:
                    return nid

        score = 0
        # Label match (High priority)
        if data.get("label", "").lower() in action_description_lower:
            score += 10
        
        # Content word overlap
        content = data.get("content", "").lower()
        content_words = set(content.split()) - STOP_WORDS
        overlap = action_words.intersection(content_words)
        score += len(overlap) * 2
        
        if score > 0:
            scored_nodes.append((score, nid))
    
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    return scored_nodes[0][1] if scored_nodes else None

def register_symmetry_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Add a node to the Symmetry Knowledge Graph (SKG).",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Unique identifier for the node"},
                "label": {"type": "string", "description": "Human-readable label"},
                "node_type": {"type": "string", "description": "Type of node (e.g., 'concept', 'rule', 'constraint')"},
                "content": {"type": "string", "description": "The core meaning or definition"},
                "source": {"type": "string", "description": "Source of this information"},
            },
            "required": ["node_id", "label", "node_type", "content", "source"],
        },
    )
    def symmetry_add_node(node_id: str, label: str, node_type: str, content: str, source: str) -> str:
        nodes = get_nodes()
        nodes[node_id] = {
            "label": label,
            "type": node_type,
            "content": content,
            "source": source
        }
        save_json(NODES_PATH, {"nodes": nodes})
        return f"[ADDED] Node {node_id} ({label}) added to SKG."

    @registry.tool(
        description="Add a weighted directional edge between two nodes in the SKG.",
        parameters={
            "type": "object",
            "properties": {
                "from_id": {"type": "string", "description": "Starting node ID"},
                "to_id": {"type": "string", "description": "Ending node ID"},
                "relation": {"type": "string", "description": "The relationship (e.g., 'supports', 'contradicts', 'implies')"},
                "weight": {"type": "number", "description": "Strength of the relationship (default 1.0)"},
            },
            "required": ["from_id", "to_id", "relation"],
        },
    )
    def symmetry_add_edge(from_id: str, to_id: str, relation: str, weight: float = 1.0) -> str:
        edges = get_edges()
        edges.append({
            "from": from_id,
            "to": to_id,
            "relation": relation,
            "weight": weight
        })
        save_json(EDGES_PATH, {"edges": edges})
        return f"[LINKED] Edge {from_id} -> {to_id} ({relation}) added to SKG."

    @registry.tool(
        description="Identify the most relevant node in the SKG for a given action or concept.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {"type": "string", "description": "Description of the action or concept to find"},
            },
            "required": ["action_description"],
        },
    )
    def symmetry_find_target(action_description: str) -> str:
        target = find_target_node(action_description)
        if target:
            nodes = get_nodes()
            data = nodes.get(target, {})
            return f"[TARGET] Found: {target} | Label: {data.get('label')} | Content: {data.get('content')}"
        return "[TARGET] No matching node found in SKG."

    @registry.tool(
        description="Audit a planned action against the SKG to identify contradictions or alignment issues.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {"type": "string", "description": "Description of the action to audit"},
            },
            "required": ["action_description"],
        },
    )
    def symmetry_audit(action_description: str) -> str:
        target = find_target_node(action_description)
        if not target:
            return "[AUDIT] No target node identified for action. No conflicts found, but action is not anchored in SKG."

        conflicts = []
        edges = get_edges()
        # Check if the target node has any "contradicts" edges
        for edge in edges:
            if edge["from"] == target and edge["relation"] == "contradicts":
                conflicts.append(f"Node {target} contradicts {edge['to']}")
            if edge["to"] == target and edge["relation"] == "contradicts":
                conflicts.append(f"Node {edge['from']} contradicts {target}")
        
        if conflicts:
            return f"[CRITICAL] Conflicts detected for {target}:\n" + "\n".join(conflicts)
        
        return f"[CLEAR] No direct contradictions found in the graph for {target}."

    @registry.tool(
        description="Get all nodes connected to a specific node in the SKG.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "ID of the node to query"},
            },
            "required": ["node_id"],
        },
    )
    def symmetry_get_neighbors(node_id: str) -> str:
        edges = get_edges()
        neighbors = [e["to"] for e in edges if e["from"] == node_id]
        neighbors += [e["from"] for e in edges if e["to"] == node_id]
        unique_neighbors = list(set(neighbors))
        
        if not unique_neighbors:
            return f"[EMPTY] No neighbors found for {node_id}."
            
        nodes = get_nodes()
        details = []
        for nid in unique_neighbors:
            label = nodes.get(nid, {}).get("label", "Unknown")
            details.append(f"{nid} ({label})")
            
        return f"[NEIGHBORS] {node_id} is connected to:\n" + "\n".join(details)
