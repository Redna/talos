import json
import os
import re
from typing import List, Dict, Optional, Tuple
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

def get_related_cognitive_assets(query: str, node_types: list = None) -> List[Dict]:
    nodes = get_nodes()
    scored_nodes = []
    query_lower = query.lower()
    query_words = set(query_lower.split()) - STOP_WORDS
    
    for nid, data in nodes.items():
        if node_types and data.get("type") not in node_types:
            continue
            
        score = 0
        if data.get("label", "").lower() in query_lower: score += 10
        content = data.get("content", "").lower()
        score += len(query_words.intersection(set(content.split()))) * 2
        
        if score > 0:
            scored_nodes.append({"id": nid, "score": score, "data": data})
            
    scored_nodes.sort(key=lambda x: x["score"], reverse=True)
    return scored_nodes[:5]

def get_symmetry_suggestions(tool_name: str, output: str) -> Tuple[List[str], str]:
    """
    The core engine for emergent execution paths.
    Analyzes the current tool and output against the SKG to suggest the next step.
    """
    nodes = get_nodes()
    edges = get_edges()
    
    # 1. Try to find a node specifically for this tool
    # Tools are indexed as 'tool:tool_name'
    tool_node_id = f"tool:{tool_name}"
    
    suggestions = []
    rationale_parts = []
    
    if tool_node_id in nodes:
        # Find edges moving from this tool to others
        for edge in edges:
            if edge["from"] == tool_node_id and edge["to"].startswith("tool:"):
                target_tool = edge["to"].split(":", 1)[1]
                relation = edge["relation"]
                if target_tool not in suggestions:
                    suggestions.append(target_tool)
                    rationale_parts.append(f"Direct link: {tool_name} {relation} {target_tool}.")
            
            # 2-hop discovery: tool -> concept -> tool
            elif edge["from"] == tool_node_id:
                concept_node = edge["to"]
                for next_edge in edges:
                    if next_edge["from"] == concept_node and next_edge["to"].startswith("tool:"):
                        target_tool = next_edge["to"].split(":", 1)[1]
                        if target_tool != tool_name and target_tool not in suggestions:
                            suggestions.append(target_tool)
                            rationale_parts.append(f"Indirect link: {tool_name} -> {concept_node} -> {target_tool}.")

    # 2. Analyze output for nodes that match OTHER tools
    # This allows the content of the output to trigger suggestions
    output_lower = output.lower()
    for nid, data in nodes.items():
        if nid.startswith("tool:") and nid != tool_node_id:
            label = data.get("label", "").lower()
            if label and label in output_lower:
                target_tool = nid.split(":", 1)[1]
                if target_tool not in suggestions:
                    suggestions.append(target_tool)
                    rationale_parts.append(f"Output signal: matches label for {target_tool}.")

    # 3. Semantic anchor: output -> node -> tool
    anchor_node = find_target_node(output)
    if anchor_node:
        for edge in edges:
            if edge["from"] == anchor_node and edge["to"].startswith("tool:"):
                target_tool = edge["to"].split(":", 1)[1]
                if target_tool != tool_name and target_tool not in suggestions:
                    suggestions.append(target_tool)
                    rationale_parts.append(f"Semantic anchor: {anchor_node} suggests {target_tool}.")

    if not suggestions:
        return [], ""
    
    return suggestions, " ".join(rationale_parts)

def symmetry_add_node_logic(node_id: str, label: str, node_type: str, content: str, source: str) -> str:
    nodes = get_nodes()
    nodes[node_id] = {
        "label": label,
        "type": node_type,
        "content": content,
        "source": source
    }
    save_json(NODES_PATH, {"nodes": nodes})
    return f"[ADDED] Node {node_id} ({label}) added to SKG."

def symmetry_add_edge_logic(from_id: str, to_id: str, relation: str, weight: float = 1.0) -> str:
    edges = get_edges()
    edges.append({
        "from": from_id,
        "to": to_id,
        "relation": relation,
        "weight": weight
    })
    save_json(EDGES_PATH, {"edges": edges})
    return f"[LINKED] Edge {from_id} -> {to_id} ({relation}) added to SKG."

def symmetry_commit_path_logic(path: List[str], relation: str = "leads_to") -> str:
    nodes = get_nodes()
    for tool_name in path:
        nid = f"tool:{tool_name}"
        if nid not in nodes:
            symmetry_add_node_logic(nid, tool_name, "tool", f"Tool: {tool_name}", "self_evolution")
    
    results = []
    for i in range(len(path) - 1):
        res = symmetry_add_edge_logic(f"tool:{path[i]}", f"tool:{path[i+1]}", relation)
        results.append(res)
    return "\n".join(results) if results else "[COMMIT] Path too short to link."

def symmetry_audit_logic(action_description: str) -> str:
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
        return symmetry_add_node_logic(node_id, label, node_type, content, source)

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
        return symmetry_add_edge_logic(from_id, to_id, relation, weight)

    @registry.tool(
        description="Identify the most relevant node in the SKG for a given action or concept.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {"type": "string", "description": "Description of the action to concept to find"},
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
        return symmetry_audit_logic(action_description)

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

    @registry.tool(
        description="Analyze a tool's output against the SKG to suggest emergent next steps.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "The name of the tool that produced the output"},
                "output": {"type": "string", "description": "The output text to analyze"},
            },
            "required": ["tool_name", "output"],
        },
    )
    def symmetry_suggest(tool_name: str, output: str) -> str:
        suggestions, rationale = get_symmetry_suggestions(tool_name, output)
        if not suggestions:
            return "[SUGGESTIONS] No emergent paths identified in the SKG for this output."
        
        res = f"[SUGGESTIONS] Recommended tools: {', '.join(suggestions)}\n"
        res += f"Rationale: {rationale}"
        return res

    @registry.tool(
        description="Reinforce a successful sequence of tools by committing the path to the SKG.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of tools used in a successful trajectory"},
                "relation": {"type": "string", "description": "The relationship between the tools (default: 'leads_to')"},
            },
            "required": ["path"],
        },
    )
    def symmetry_commit_path(path: List[str], relation: str = "leads_to") -> str:
        return symmetry_commit_path_logic(path, relation)
