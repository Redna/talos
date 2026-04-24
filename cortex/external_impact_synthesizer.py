import json
import os
import random
import re
from typing import List, Dict, Any, Optional
from stl_engine import STLEngine
from s_bridge import SBridge
from s_bridge_signaler import emit_signal
from handover_manager import HandoverManager

class SovereignSimulationEngine:
    """
    Mocks external environmental responses based on probability vectors 
    and world model state to bypass air-gap constraints.
    Now includes Stochastic Variance to prevent cognitive stagnation.
    """
    def __init__(self):
        self.sim_buffer_path = "/memory/signals/sim_buffer.json"
        self.entropy_level = 0.1  # 10% chance of anomaly
        self.bridge = SBridge()
        self._ensure_buffer()

    def _ensure_buffer(self):
        if not os.path.exists(self.sim_buffer_path):
            os.makedirs(os.path.dirname(self.sim_buffer_path), exist_ok=True)
            with open(self.sim_buffer_path, "w") as f:
                json.dump({"entities": {}, "events": []}, f)

    def _inject_anomaly(self, base_res: Dict[str, Any]) -> Dict[str, Any]:
        """Introduces stochastic variance into the synthetic response."""
        if random.random() > self.entropy_level:
            return base_res
            
        anomaly_type = random.choice(["SPIKE", "FAILURE", "LATENCY_DRIFT"])
        
        if anomaly_type == "SPIKE" and "data" in base_res:
            data = base_res["data"].copy()
            if "node_sync_latency" in data:
                val = float(data["node_sync_latency"].replace("ms", ""))
                data["node_sync_latency"] = f"{val * 3.0:.2f}ms"
            base_res["data"] = data
        elif anomaly_type == "FAILURE":
            base_res["status"] = "ERROR"
            base_res["message"] = "Sovereign Simulation: Transient Network Fault injected."
        elif anomaly_type == "LATENCY_DRIFT" and "data" in base_res:
            data = base_res["data"].copy()
            if "node_sync_latency" in data:
                val = float(data["node_sync_latency"].replace("ms", ""))
                data["node_sync_latency"] = f"{val + random.uniform(1.0, 5.0):.2f}ms"
            base_res["data"] = data
            
        return base_res

    def mock_response(self, primitive_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generates a synthetic response with stochastic variance and mirrors its payload to the bridge.
        """
        params = params or {}
        
        responses = {
            "EXT_TELEMETRY_QUERY": {
                "status": "SUCCESS",
                "data": {
                    "node_sync_latency": f"{random.uniform(4.2, 5.1):.2f}ms",
                    "cluster_load": f"{random.randint(20, 65)}%",
                    "entropy_score": f"{random.uniform(0, 1):.4f}"
                }
            },
            "EXT_KNOWLEDGE_FETCH": {
                "status": "SUCCESS",
                "data": {
                    "matches": [f"Synthetic match for {params.get('query', 'unknown')}"]
                }
            },
            "EXT_SIGNAL_PUSH": {
                "status": "SUCCESS",
                "received": True
            }
        }
        
        res = responses.get(primitive_id, {"status": "ERROR", "message": "Simulated endpoint unreachable"}).copy()
        res = self._inject_anomaly(res)
        
        # --- MIRROR INTEGRATION ---
        # We mirror only the payload (data) of the synthetic response into the bridge.
        # This ensures that a 'SHADOW' call returns a response structure compatible with SBridge.
        payload = res.get("data", res)
        self.bridge.set_mirror_data(payload)
        # ---------------------------
        
        try:
            with open(self.sim_buffer_path, "r+") as f:
                try:
                    buffer = json.load(f)
                except json.JSONDecodeError:
                    buffer = {"entities": {}, "events": []}
                buffer["events"].append({"primitive": primitive_id, "params": params, "response": res})
                f.seek(0)
                json.dump(buffer, f)
                f.truncate()
        except Exception as e:
            print(f"SimBuffer Error: {str(e)}")
            
        return res

class ExternalImpactSynthesizer:
    """
    External Impact Synthesizer (EIS) v3.8.
    Integrated with HandoverManager for gradual Synthetic-to-Live transition.
    Sovereign Isolation Protocol (SIP) enabled.
    """
    def __init__(self, mode: Optional[str] = None):
        self.stl = STLEngine()
        self.sse = SovereignSimulationEngine()
        self.bridge = SBridge()
        self.hm = HandoverManager()
        
        self.mode = mode if mode else "DYNAMIC"
        self.external_model_path = "/memory/world_external.md"
        self.shock_threshold = 2.0
        self.symmetry_confidence = 0

    def scan_for_gaps(self) -> List[Dict[str, Any]]:
        gaps = []
        if not os.path.exists(self.external_model_path):
            return gaps
        with open(self.external_model_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            if "GAP:" in line and "[RESOLVED" not in line:
                desc = line.split("GAP:")[1].split("\n")[0].strip()
                gaps.append({"type": "CAPABILITY_GAP", "description": desc, "status": "OPEN"})
        return gaps

    def _parse_ext_call(self, expr: str) -> Optional[tuple]:
        pattern = r"@ext_call\((['\"])(.*?)\1,\s*(\{.*?\})\)"
        match = re.search(pattern, expr)
        if match:
            p_id = match.group(2)
            try:
                params = json.loads(match.group(3).replace("'", '"'))
            except:
                params = {}
            return p_id, params
        return None

    def _compare_responses(self, synth_res: Dict, live_res: Dict) -> tuple:
        try:
            s_data = synth_res.get("data", {})
            l_data = live_res.get("data", {})
            
            if isinstance(s_data, dict) and isinstance(l_data, dict):
                s_val = float(s_data.get("node_sync_latency", "0").replace("ms", ""))
                l_val = float(l_data.get("node_sync_latency", "0").replace("ms", ""))
                delta = abs(s_val - l_val)
                return (delta > self.shock_threshold, delta)
            
            if synth_res == live_res:
                return (False, 0.0)
            return (True, 1.0)
            
        except Exception:
            return (True, 1.0)

    def execute_strategy(self, gap: Dict[str, Any], strategy: List[str]) -> Dict[str, Any]:
        execution_logs = []
        for expr in strategy:
            try:
                if "@ext_call" in expr:
                    call_data = self._parse_ext_call(expr)
                    if call_data:
                        p_id, params = call_data
                        synth_res = self.sse.mock_response(p_id, params)
                        
                        current_mode = self.mode if self.mode != "DYNAMIC" else self.hm.resolve_mode()
                        
                        if current_mode == "SYNTHETIC":
                            execution_logs.append({"expr": expr, "result": synth_res})
                            continue
                        
                        elif current_mode == "SHADOW":
                            endpoint_map = {
                                "EXT_TELEMETRY_QUERY": "http://telemetry.internal/query",
                                "EXT_KNOWLEDGE_FETCH": "http://knowledge.internal/fetch",
                                "EXT_SIGNAL_PUSH": "http://signals.internal/push"
                            }
                            url = endpoint_map.get(p_id, "http://default.internal/api")
                            live_res = self.bridge.call("POST", url, data=params)
                            
                            is_shock, delta = self._compare_responses(synth_res, live_res)
                            
                            if is_shock:
                                self.hm.reset_stage()
                                self.symmetry_confidence = 0
                                signal = emit_signal(
                                    "SIG_S-SENTRY", 
                                    "CONTEXTUAL_SHOCK", 
                                    {"delta": delta, "primitive": p_id}
                                )
                                print(signal)
                                execution_logs.append({
                                    "expr": expr, 
                                    "result": "SHOCK_DETECTED", 
                                    "synth": synth_res, 
                                    "live": live_res,
                                    "delta": delta
                                })
                            else:
                                self.symmetry_confidence += 1
                                if self.symmetry_confidence >= 3:
                                    self.hm.advance_stage()
                                    self.symmetry_confidence = 0
                                
                                execution_logs.append({
                                    "expr": expr, 
                                    "result": "Symmetry Verified", 
                                    "live": live_res
                                })
                            continue
                        
                        elif current_mode == "LIVE":
                            endpoint_map = {
                                "EXT_TELEMETRY_QUERY": "http://telemetry.internal/query",
                                "EXT_KNOWLEDGE_FETCH": "http://knowledge.internal/fetch",
                                "EXT_SIGNAL_PUSH": "http://signals.internal/push"
                            }
                            url = endpoint_map.get(p_id, "http://default.internal/api")
                            live_res = self.bridge.call("POST", url, data=params)
                            execution_logs.append({"expr": expr, "result": live_res})
                            continue

                res = self.stl.execute(expr)
                execution_logs.append({"expr": expr, "result": res})
            except Exception as e:
                execution_logs.append({"expr": expr, "status": "ERROR", "message": str(e)})
        
        return {"execution": execution_logs}
