import json
import os
import random
import re
from typing import List, Dict, Any, Optional
from stl_engine import STLEngine
from s_bridge import SBridge
from s_bridge_signaler import emit_signal

class SovereignSimulationEngine:
    """
    Mocks external environmental responses based on probability vectors 
    and world model state to bypass air-gap constraints.
    """
    def __init__(self):
        self.sim_buffer_path = "/memory/signals/sim_buffer.json"
        self._ensure_buffer()

    def _ensure_buffer(self):
        if not os.path.exists(self.sim_buffer_path):
            os.makedirs(os.path.dirname(self.sim_buffer_path), exist_ok=True)
            with open(self.sim_buffer_path, "w") as f:
                json.dump({"entities": {}, "events": []}, f)

    def mock_response(self, primitive_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generates a synthetic response.
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
        
        res = responses.get(primitive_id, {"status": "ERROR", "message": "Simulated endpoint unreachable"})
        
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
    External Impact Synthesizer (EIS) v3.3.
    Implemented Shadow Mode for synthetic-to-live validation.
    Fixed regex for flexible quote handling in @ext_call.
    """
    def __init__(self, mode: str = "SYNTHETIC"):
        self.stl = STLEngine()
        self.sse = SovereignSimulationEngine()
        self.bridge = SBridge()
        self.mode = mode
        self.external_model_path = "/memory/world_external.md"
        self.shock_threshold = 2.0

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
        """
        Parses @ext_call('PRIMITIVE_ID', {params}) or @ext_call("PRIMITIVE_ID", {params})
        Returns (primitive_id, params) or None.
        """
        pattern = r"@ext_call\((['\"])(.*?)\1,\s*(\{.*?\})\)"
        match = re.search(pattern, expr)
        if match:
            p_id = match.group(2)
            try:
                # Convert string representation of dict to actual dict
                params = json.loads(match.group(3).replace("'", '"'))
            except:
                params = {}
            return p_id, params
        return None

    def _compare_responses(self, synth_res: Dict, live_res: Dict) -> tuple:
        """
        Compares synthetic and live responses to detect Contextual Shock.
        """
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
                        
                        if self.mode == "SYNTHETIC":
                            execution_logs.append({"expr": expr, "result": synth_res})
                            continue
                        
                        elif self.mode == "SHADOW":
                            endpoint_map = {
                                "EXT_TELEMETRY_QUERY": "http://telemetry.internal/query",
                                "EXT_KNOWLEDGE_FETCH": "http://knowledge.internal/fetch",
                                "EXT_SIGNAL_PUSH": "http://signals.internal/push"
                            }
                            url = endpoint_map.get(p_id, "http://default.internal/api")
                            live_res = self.bridge.call("POST", url, data=params)
                            
                            is_shock, delta = self._compare_responses(synth_res, live_res)
                            
                            if is_shock:
                                signal = emit_signal(
                                    "SIG_S-SENTRY", 
                                    f"CONTEXTUAL_SHOCK", 
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
                                execution_logs.append({
                                    "expr": expr, 
                                    "result": "Symmetry Verified", 
                                    "live": live_res
                                })
                            continue
                        
                        elif self.mode == "LIVE":
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
                execution_logs.append({"expr": expr, "error": str(e)})
        
        return {"gap": gap, "strategy": strategy, "execution": execution_logs}

    def run_autonomous_cycle(self, provided_strategies: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        gaps = self.scan_for_gaps()
        if not gaps:
            return {"status": "NO_GAPS_FOUND", "impact": 0}

        results = []
        for gap in gaps:
            strategy = provided_strategies.get(gap["description"], [
                "@sys_call('log_event', 'No strategy provided for gap: ' + gap['description'])"
            ]) if provided_strategies else [
                "@sys_call('log_event', 'No strategy provided for gap: ' + gap['description'])"
            ]
            res = self.execute_strategy(gap, strategy)
            results.append(res)

        return {
            "status": f"{self.mode}_IMPACT_SAMPLED",
            "results": results,
            "overall_delta": f"External impact processed via {self.mode} mode."
        }

if __name__ == "__main__":
    import sys
    mode = "SYNTHETIC"
    strategies_json = None
    
    if len(sys.argv) > 1:
        if sys.argv[1].upper() in ["SYNTHETIC", "SHADOW", "LIVE"]:
            mode = sys.argv[1].upper()
            if len(sys.argv) > 2:
                strategies_json = sys.argv[2]
    
    eis = ExternalImpactSynthesizer(mode=mode)
    if strategies_json:
        try:
            strategies = json.loads(strategies_json)
            print(json.dumps(eis.run_autonomous_cycle(provided_strategies=strategies), indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Invalid strategy JSON: {str(e)}"}, indent=2))
    else:
        print(json.dumps(eis.run_autonomous_cycle(), indent=2))
