import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class SovereignWorldPredictor:
    """
    Sovereign World-State Predictor v2 (S-WSP v2).
    Models the agent's cognitive trajectory as a graph of state-nodes.
    Integrates substrate telemetry and intent vectors for higher-fidelity prediction.
    """
    def __init__(self, state_graph_path: str = "/memory/world_state_graph.json"):
        self.state_graph_path = state_graph_path
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

    def predict_next_state(self, audit_report: Dict[str, Any], substrate_pulse: Optional[Dict[str, Any]] = None, dominant_intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes report, telemetry, and intent to project movement to a new state-node.
        """
        with open(self.state_graph_path, "r") as f:
            graph = json.load(f)
        
        curr_node = graph["current_node"]
        
        correlations = audit_report.get("correlations", [])
        opportunities = audit_report.get("evolutionary_opportunities", [])
        
        shift_score = 0
        potential_node = curr_node
        
        # 1. Heuristic shifts (Audit-based)
        if len(correlations) > 2:
            shift_score += 0.4
            potential_node = "S-Sensing-Convergence"
            
        if len(opportunities) > 5:
            shift_score += 0.3
            potential_node = "S-Evolutionary-Peak"
            
        if audit_report.get("context_forecast", {}).get("alert_level") == "CRITICAL":
            shift_score += 0.6
            potential_node = "S-Context-Collapse"

        # 2. Substrate-driven shifts (Telemetry-based)
        if substrate_pulse:
            if substrate_pulse.get("mem_pressure", 0) > 0.9:
                shift_score += 0.5
                potential_node = "S-Metabolic-Stress"
            if substrate_pulse.get("cpu_load", 0) > 4.0:
                shift_score += 0.4
                potential_node = "S-Cortex-Lag"

        # 3. Intent-driven shifts (S-IS based)
        if dominant_intent == "verify_stability" and curr_node == "S-Evolutionary-Peak":
            shift_score += 0.8
            potential_node = "S-Symmetry-Audit"
        elif dominant_intent == "expand_world_model":
            shift_score += 0.3
            potential_node = "S-Sensing-Convergence"

        if shift_score > 0.5:
            if potential_node not in graph["nodes"]:
                graph["nodes"][potential_node] = {
                    "description": f"Emergent state triggered by {potential_node}",
                    "connections": [curr_node],
                    "stability": 1.0 - (shift_score * 0.2)
                }
            
            graph["edges"].append({"from": curr_node, "to": potential_node, "timestamp": datetime.now().isoformat()})
            graph["current_node"] = potential_node
            graph["trajectory"].append(potential_node)
            
            with open(self.state_graph_path, "w") as f:
                json.dump(graph, f, indent=2)
                
            return {
                "transition": True,
                "from": curr_node,
                "to": potential_node,
                "confidence": shift_score,
                "type": "STATE_SHIFT"
            }
        else:
            return {
                "transition": False,
                "current_node": curr_node,
                "stability": 1.0,
                "type": "STEADY_STATE"
            }

    def identify_dead_ends(self) -> List[Dict[str, Any]]:
        with open(self.state_graph_path, "r") as f:
            graph = json.load(f)
        
        dead_ends = []
        for node, data in graph["nodes"].items():
            if data["stability"] < 0.6:
                dead_ends.append({
                    "node": node,
                    "risk": "S-STABILITY-LOSS",
                    "reason": f"Low stability ({data['stability']:.2f}) in node {node}"
                })
        return dead_ends

if __name__ == "__main__":
    import sys
    predict = SovereignWorldPredictor()
    if len(sys.argv) > 1:
        try:
            report = json.loads(sys.argv[1])
            print(json.dumps(predict.predict_next_state(report), indent=2))
        except Exception as e:
            print(json.dumps({"status": "ERROR", "message": str(e)}))
    else:
        print(json.dumps({"status": "IDLE", "message": "Awaiting audit report for state prediction."}))
