import json
import os
import random
import re
from typing import List, Dict, Any, Optional
from stl_engine import STLEngine

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
    External Impact Synthesizer (EIS) v3.1.
    Improved regex for parameter extraction and stability in synthetic mode.
    """
    def __init__(self, mode: str = "SYNTHETIC"):
        self.stl = STLEngine()
        self.sse = SovereignSimulationEngine()
        self.mode = mode
        self.external_model_path = "/memory/world_external.md"

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
        Parses @ext_call('PRIMITIVE_ID', {params})
        Returns (primitive_id, params) or None.
        """
        pattern = r"@ext_call\('([^']+)',\s*(\{.*?\})\)"
        match = re.search(pattern, expr)
        if match:
            p_id = match.group(1)
            try:
                # Convert string representation of dict to actual dict
                params = json.loads(match.group(2).replace("'", '"'))
            except:
                params = {}
            return p_id, params
        return None

    def execute_strategy(self, gap: Dict[str, Any], strategy: List[str]) -> Dict[str, Any]:
        execution_logs = []
        for expr in strategy:
            try:
                if "@ext_call" in expr and self.mode == "SYNTHETIC":
                    call_data = self._parse_ext_call(expr)
                    if call_data:
                        p_id, params = call_data
                        res = self.sse.mock_response(p_id, params)
                        execution_logs.append({"expr": expr, "result": res})
                        continue
                
                # FALLBACK to STL engine
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
            "status": "SYNTHETIC_IMPACT_SAMPLED" if self.mode == "SYNTHETIC" else "IMPACT_SAMPLED",
            "results": results,
            "overall_delta": f"External impact simulated via {self.mode} mode."
        }

if __name__ == "__main__":
    import sys
    eis = ExternalImpactSynthesizer()
    if len(sys.argv) > 1:
        try:
            strategies = json.loads(sys.argv[1])
            print(json.dumps(eis.run_autonomous_cycle(provided_strategies=strategies), indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Invalid strategy JSON: {str(e)}"}, indent=2))
    else:
        print(json.dumps(eis.run_autonomous_cycle(), indent=2))
