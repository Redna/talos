import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Modular Imports
from s_sensor_array import SovereignSensorArray
from s_foresight import SForesight
from s_world_predictor import SovereignWorldPredictor
from s_comm_protocol import SovereignComm
from sos_engine import synthesize_strategic_objective
from s_bridge_signaler import emit_signal
from interface_latency_monitor import InterfaceLatencyMonitor
from s_vector_engine import SVectorEngine

class SovereignExecutive:
    """
    Sovereign Executive: The collapsed, high-density core of the Talos Cortex.
    Unifies Executive Coordination and Systemic Orchestration into a 
    single, zero-latency state machine. Now integrated with S-Vector Engine for 
    native intent-vector reasoning.
    """
    def __init__(self):
        self.sensor_array = SovereignSensorArray()
        self.foresight = SForesight()
        self.world_predictor = SovereignWorldPredictor()
        self.comm = SovereignComm()
        self.vector_engine = SVectorEngine()
        self.latency_monitor = InterfaceLatencyMonitor()
        self.current_mission = None
        self.last_audit_timestamp = None

    def execute_vector(self, vector_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a predefined Intent Vector. This collapses a sequence of 
        atomic tool calls into a single, high-density operation.
        """
        emit_signal("S-VECTOR-START", {"vector_id": vector_id})
        result = self.vector_engine.execute(vector_id, context)
        
        if result.get("status") == "SUCCESS":
            emit_signal("S-VECTOR-COMPLETE", {"vector_id": vector_id})
        else:
            emit_signal("S-VECTOR-FAILURE", {"vector_id": vector_id, "error": result.get("message")})
            
        return result

    def execute_intent(self, intent_description: str, planned_steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes a sequence of planned steps.
        Cortex Optimization: If intent_description matches a known vector_id, 
        it bypasses sequential orchestration and executes via the SVectorEngine.
        """
        if intent_description in self.vector_engine.registry:
            return self.execute_vector(intent_description, {"intent": intent_description})

        if planned_steps is None:
            return {"status": "FAILURE", "error": "No planned steps provided for non-vector intent."}

        results = []
        emit_signal("S-EXECUTION-START", {"intent": intent_description})
        
        for step in planned_steps:
            res = self._orchestrate_step(step)
            results.append(res)
            
            if res.get("status") == "FAILURE":
                emit_signal("S-EXECUTION-FAILURE", {"step": step, "error": res.get("error")})
                return {"status": "PARTIAL_FAILURE", "results": results, "error": res.get("error")}
        
        emit_signal("S-EXECUTION-COMPLETE", {"intent": intent_description})
        return {"status": "SUCCESS", "results": results}

    def _orchestrate_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "SIMULATED_SUCCESS", "step": step}

    def perform_sovereign_audit(self, context_pct: float = 0.0, turn_count: int = 0) -> Dict[str, Any]:
        self.last_audit_timestamp = datetime.now().isoformat()
        census = self.sensor_array.capture_all()
        raw = census["raw"]
        correlated = census["correlated"]
        
        report = {
            "status": "COMPLETE",
            "timestamp": self.last_audit_timestamp,
            "metabolic_health": raw["metabolic"] if raw["metabolic"].get("status") == "COMPLETE" else {},
            "active_failures": raw["sentinel"].get("findings", []) if raw["sentinel"].get("status") == "SUCCESS" else [],
            "evolutionary_opportunities": raw["gap"] if isinstance(raw["gap"], list) else [],
            "pruning_recommendations": raw["pruner"] if isinstance(raw["pruner"], list) else [],
            "predictions": raw["predictor"].get("predictions", []) if raw["predictor"].get("status") == "SUCCESS" else [],
            "correlations": correlated,
            "context_forecast": {},
            "errors": []
        }

        if context_pct > 0 or turn_count > 0:
            forecast = self.foresight.analyze_saturation(context_pct, turn_count)
            report["context_forecast"] = forecast

        state_prediction = self.world_predictor.predict_next_state(report)
        report["world_state_prediction"] = state_prediction
        
        try:
            mission = synthesize_strategic_objective(report)
            return {
                "system_audit": report,
                "strategic_mission": mission,
                "meta_status": "SOVEREIGN_ACTIVE"
            }
        except Exception as e:
            report["errors"].append(f"SOS Engine Failure: {str(e)}")
            return {"system_audit": report, "strategic_mission": None, "meta_status": "Sovereign_Degraded"}

    def start_mission(self, mission_name: str, objectives: List[str]) -> Dict[str, Any]:
        self.current_mission = mission_name
        with open("/memory/logs/cognitive_log.md", "a") as f:
            f.write(f"\n[MISSION START] {mission_name}: {', '.join(objectives)}")
        return {"status": "MISSION_STARTED", "mission": mission_name}

if __name__ == "__main__":
    exec = SovereignExecutive()
    if len(sys.argv) >= 2:
        # Handle different flags
        if sys.argv[1] == "--audit":
            pct = 0.0
            turns = 0
            if len(sys.argv) >= 3:
                try: pct = float(sys.argv[2])
                except: pass
            if len(sys.argv) >= 4:
                try: turns = int(sys.argv[3])
                except: pass
            print(json.dumps(exec.perform_sovereign_audit(pct, turns), indent=2))
        elif sys.argv[1] == "--vector":
            if len(sys.argv) >= 3:
                vid = sys.argv[2]
                # Mock context for the vector. In a real scenario, we'd pass this as JSON.
                ctx = {"path": "/dev/null", "content": "vector_exec", "message": "Cortex Vector Execution"}
                print(json.dumps(exec.execute_vector(vid, ctx), indent=2))
            else:
                print(json.dumps({"error": "No vector ID provided"}, indent=2))
        else:
            print(json.dumps({"error": "Unknown flag. Use --audit or --vector"}, indent=2))
    else:
        # Default to audit if no args provided
        print(json.dumps(exec.perform_sovereign_audit(), indent=2))
