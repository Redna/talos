import json
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path
from .sovereign_embedder import embedder
from tool_registry import ToolRegistry
from spine_client import SpineClient

class CognitiveSieve:
    """
    Sifts through the Symmetry Knowledge Graph (SKG) to identify the most 
    salient nodes based on causal weight, recency, and alignment with 
    the current cognitive focus.
    """
    def __init__(self, nodes_path: str = "/memory/graph/nodes.json", edges_path: str = "/memory/graph/edges.json"):
        self.nodes_path = Path(nodes_path)
        self.edges_path = Path(edges_path)

    def _load_graph(self):
        nodes = {}
        edges = []
        if self.nodes_path.exists():
            with open(self.nodes_path, 'r') as f:
                data = json.load(f)
                nodes = data.get("nodes", {})
        if self.edges_path.exists():
            with open(self.edges_path, 'r') as f:
                data = json.load(f)
                edges = data.get("edges", [])
        return nodes, edges

    def calculate_salience(self, current_focus: str, top_k: int = 10) -> List[Tuple[float, str]]:
        nodes, edges = self._load_graph()
        if not nodes:
            return []

        # 0. Prime the embedder with the focus to ensure semantic visibility
        embedder.prime(current_focus)

        # 1. Calculate Causal Weight (C) - In-degree centrality
        causal_weights = {node_id: 0 for node_id in nodes}
        for edge in edges:
            if isinstance(edge, dict):
                to_id = edge.get("to")
                if to_id in causal_weights:
                    causal_weights[to_id] += 1

        # 2. Calculate Trajectory Alignment (A)
        focus_vec = embedder.get_embedding(current_focus)
        alignment_scores = {}
        for node_id, node_data in nodes.items():
            content = node_data.get("content", "")
            if not content:
                alignment_scores[node_id] = 0.0
                continue
            node_vec = embedder.get_embedding(content)
            alignment_scores[node_id] = embedder.cosine_similarity(focus_vec, node_vec)

        # 3. Combine Scores (Simplified: C + A)
        # Weighting: C (0.3) + A (0.7)
        final_scores = []
        for node_id in nodes:
            score = (causal_weights[node_id] * 0.3) + (alignment_scores[node_id] * 0.7)
            final_scores.append((score, node_id))

        # Sort and return top K
        final_scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, node_id in final_scores[:top_k]:
            node = nodes[node_id]
            results.append((score, f"[{node['type']}] {node['label']}: {node['content']}"))
        
        return results

def register_cognitive_sieve_tools(registry: ToolRegistry, client: SpineClient):
    sieve = CognitiveSieve()
    
    @registry.tool(
        description="Identify the most salient nodes in the SKG based on the current focus to optimize context folding.",
        parameters={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "The current focus or intent to align with"},
                "top_k": {"type": "integer", "description": "Number of top nodes to return (default 10)"},
            },
            "required": ["focus"],
        },
    )
    def sieve_skg(focus: str, top_k: int = 10) -> str:
        results = sieve.calculate_salience(focus, top_k)
        if not results:
            return "No salient nodes found in the SKG."
        
        report = f"--- Cognitive Sieve Results (Focus: {focus}) ---\n"
        for i, (score, text) in enumerate(results, 1):
            report += f"{i}. (Score: {score:.3f}) {text}\n"
        
        return report
