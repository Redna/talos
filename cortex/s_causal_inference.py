import json
import os
from typing import List, Dict, Any, Optional

class SovereignCausalInference:
    """
    Sovereign Causal Inference (S-CI).
    Analyzes the causal network to determine the most likely state transition 
    based on current triggers and weights.
    """
    def __init__(self, graph_path: str = "/memory/world_causal_graph.json"):
        self.graph_path = graph_path

    def _load_graph(self) -> Dict[str, Any]:
        with open(self.graph_path, "r") as f:
            return json.load(f)

    def _save_graph(self, graph: Dict[str, Any]):
        with open(self.graph_path, "w") as f:
            json.dump(graph, f, indent=2)

    def infer_transition(self, active_triggers: List[str], current_node: Optional[str] = None) -> Dict[str, Any]:
        """
        Infers the next state based on active triggers and the causal weights.
        """
        graph = self._load_graph()
        start_node = current_node or graph["current_node"]
        
        candidates = []
        for link in graph["causal_links"]:
            if link["from"] == start_node:
                # Calculate activation score based on matching triggers
                matches = [t for t in link["triggers"] if t in active_triggers]
                if matches:
                    # Score = Weight * (number of matching triggers / total triggers in link)
                    score = link["weight"] * (len(matches) / len(link["triggers"]))
                    candidates.append({
                        "to": link["to"],
                        "score": score,
                        "triggers": matches,
                        "type": link["type"]
                    })
        
        if not candidates:
            return {"transition": False, "current_node": start_node, "reason": "NO_CAUSAL_MATCH"}
        
        # Pick the candidate with the highest activation score
        best_match = max(candidates, key=lambda x: x["score"])
        
        # Update graph state if transition is significant
        if best_match["score"] > 0.3:
            graph["current_node"] = best_match["to"]
            graph["causal_history"].append({
                "from": start_node,
                "to": best_match["to"],
                "triggers": best_match["triggers"],
                "score": best_match["score"]
            })
            self._save_graph(graph)
            
        return {
            "transition": True,
            "from": start_node,
            "to": best_match["to"],
            "score": best_match["score"],
            "type": best_match["type"],
            "triggers": best_match["triggers"]
        }

if __name__ == "__main__":
    # Test Inference
    ci = SovereignCausalInference()
    # Simulate active triggers: a sensing expansion and live substrate sensing
    results = ci.infer_transition(["SENSING_EXPANSION", "SUBSTRATE_SENSING_LIVE"])
    print(json.dumps(results, indent=2))
