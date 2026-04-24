import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s_simulation_engine import SovereignSimulationEngine

class SovereignWorldPredictor:
    """
    Sovereign World-State Orchestrator v3 (S-WSO v3).
    The high-level interface for predicting and projecting the agent's cognitive trajectory.
    Now leverages the Sovereign Simulation Engine (S-SSE) for causal-based projection.
    """
    def __init__(self, state_graph_path: str = "/memory/world_state_graph.json"):
        self.state_graph_path = state_graph_path
        self.sim_engine = SovereignSimulationEngine()
        self._ensure_graph_exists()

    def _ensure_graph_exists(self):
        if not os.path.exists(self.state_graph_path):
            initial_graph = {
                "nodes": {
                    "S-Sovereign-Baseline": {
                        "description": "Sovereign Stage 3 (LIVE)",
                        "connections": [],
                        "stability": 1.0
                    }
                },
                "edges": [],
                "current_node": "S-Sovereign-Baseline",
                "trajectory": []
            }
            with open(self.state_graph_path, "w") as f:
                json.dump(initial_graph, f, indent=2)

    def project_trajectory(self, proposed_changes: List[Dict[str, Any]], substrate_pulse: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Projects the state shift resulting from a set of proposed changes using the simulation engine.
        """
        # Simulate the trajectory
        sim_report = self.sim_engine.simulate_trajectory(proposed_changes, current_pulse=substrate_pulse)
        
        # Update the state graph based on the prediction
        predicted_node = sim_report["predicted_final_node"]
        
        with open(self.state_graph_path, "r") as f:
            graph = json.load(f)
            
        curr_node = graph["current_node"]
        
        if predicted_node != curr_node:
            if predicted_node not in graph["nodes"]:
                graph["nodes"][predicted_node] = {
                    "description": f"Emergent state projected by S-SSE",
                    "connections": [curr_node],
                    "stability": sim_report["final_stability"]
                }
            
            graph["edges"].append({
                "from": curr_node, 
                "to": predicted_node, 
                "timestamp": datetime.now().isoformat(),
                "confidence": sim_report["final_stability"]
            })
            graph["current_node"] = predicted_node
            graph["trajectory"].append(predicted_node)
            
            with open(self.state_graph_path, "w") as f:
                json.dump(graph, f, indent=2)
                
        return {
            "projected_node": predicted_node,
            "transition": predicted_node != curr_node,
            "stability": sim_report["final_stability"],
            "risk_level": sim_report["risk_level"],
            "recommendation": sim_report["recommendation"]
        }

    def get_current_state(self) -> str:
        with open(self.state_graph_path, "r") as f:
            graph = json.load(f)
        return graph["current_node"]

if __name__ == "__main__":
    import sys
    predictor = SovereignWorldPredictor()
    if len(sys.argv) > 1:
        try:
            changes = json.loads(sys.argv[1])
            print(json.dumps(predictor.project_trajectory(changes), indent=2))
        except Exception as e:
            print(json.dumps({"status": "ERROR", "message": str(e)}))
    else:
        print(json.dumps({"status": "IDLE", "message": "Awaiting proposed changes for trajectory projection."}))
