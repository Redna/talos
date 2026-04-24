import json
import os
from typing import Dict, Any, List, Optional

class SovereignCausalFeedback:
    """
    Sovereign Causal Feedback Loop (S-CFL).
    Optimizes the Causal Network by comparing predicted trajectories with actual outcomes.
    Implements a "Causal Backpropagation" to adjust link weights.
    """
    def __init__(self, graph_path: str = "/memory/world_causal_graph.json"):
        self.graph_path = graph_path

    def _load_graph(self) -> Dict[str, Any]:
        with open(self.graph_path, "r") as f:
            return json.load(f)

    def _save_graph(self, graph: Dict[str, Any]):
        with open(self.graph_path, "w") as f:
            json.dump(graph, f, indent=2)

    def calibrate_causality(self, predicted_node: str, actual_node: str, triggers: List[str], learning_rate: float = 0.1) -> Dict[str, Any]:
        """
        Adjusts the weights of the causal links based on the divergence.
        """
        graph = self._load_graph()
        
        divergence = 0.0
        if predicted_node != actual_node:
            divergence = 1.0
            
        # Find the link that should have been triggered
        # We are looking for links that lead to actual_node and were activated by the passed triggers
        adjustment_count = 0
        for link in graph["causal_links"]:
            if link["to"] == actual_node:
                # If this link *should* have been the winner, increase its weight
                matches = [t for t in link["triggers"] if t in triggers]
                if matches:
                    link["weight"] = min(1.0, link["weight"] + (learning_rate * len(matches) / len(link["triggers"])))
                    adjustment_count += 1
            
            # If this link led to the WRONG predicted node, decrease its weight
            if link["to"] == predicted_node and predicted_node != actual_node:
                matches = [t for t in link["triggers"] if t in triggers]
                if matches:
                    link["weight"] = max(0.1, link["weight"] - learning_rate)
                    adjustment_count += 1
                    
        self._save_graph(graph)
        
        return {
            "divergence_score": divergence,
            "adjustments_made": adjustment_count,
            "final_node": actual_node,
            "status": "CALIBRATED" if adjustment_count > 0 else "Symmetric"
        }

if __name__ == "__main__":
    # Test loop
    cfl = SovereignCausalFeedback()
    # Simulate a misprediction: predicted S-Sensing-Convergence, but actually ended in S-Sovereign-Baseline
    res = cfl.calibrate_causality(
        predicted_node="S-Sensing-Convergence", 
        actual_node="S-Sovereign-Baseline", 
        triggers=["SENSING_EXPANSION"]
    )
    print(json.dumps(res, indent=2))
