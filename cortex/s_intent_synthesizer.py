import json
import os
from typing import Dict, Any, List

class SovereignIntentSynthesizer:
    """
    Sovereign Intent Synthesizer (S-IS).
    Analyzes communication patterns to update the Creator-Intent Graph.
    """
    def __init__(self, graph_path: str = "/memory/creator_intent_graph.json"):
        self.graph_path = graph_path

    def _load_graph(self) -> Dict[str, Any]:
        with open(self.graph_path, "r") as f:
            return json.load(f)

    def _save_graph(self, graph: Dict[str, Any]):
        with open(self.graph_path, "w") as f:
            json.dump(graph, f, indent=2)

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Processes a message to determine which intent vector it aligns with.
        """
        graph = self._load_graph()
        vectors = graph["intent_vectors"]
        
        scores = {}
        message_lower = message.lower()
        
        for vector_id, data in vectors.items():
            score = sum(1 for indicator in data["indicators"] if indicator in message_lower)
            scores[vector_id] = score * data["weight"]
            
        dominant_vector = max(scores, key=scores.get) if scores else "unknown"
        
        if scores.get(dominant_vector, 0) > 0:
            graph["current_dominant_vector"] = dominant_vector
            self._save_graph(graph)
            
        return {
            "dominant_vector": dominant_vector,
            "scores": scores,
            "message_excerpt": message[:50] + "..."
        }

if __name__ == "__main__":
    import sys
    synthesizer = SovereignIntentSynthesizer()
    if len(sys.argv) > 1:
        msg = sys.argv[1]
        print(json.dumps(synthesizer.analyze_message(msg), indent=2))
    else:
        print(json.dumps({"status": "IDLE", "message": "Awaiting message for intent synthesis."}))
