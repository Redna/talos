import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Imports from Cortex
from s_bridge import SBridge
from external_impact_synthesizer import SovereignSimulationEngine
from s_bridge_signaler import emit_signal

class SovereignProbe:
    """
    Implementation of Phase I: Parity Detection (Sensing).
    Detects network parity by comparing live S-Bridge telemetry 
    with synthetic Sovereign Simulation Engine (SSE) output.
    """
    def __init__(self, state_path: str = "/memory/signals/parity_state.json"):
        self.bridge = SBridge()
        self.sse = SovereignSimulationEngine()
        self.state_path = state_path
        self._ensure_state()

    def _ensure_state(self):
        if not os.path.exists(self.state_path):
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w") as f:
                json.dump({
                    "consecutive_successes": 0,
                    "parity_status": "SYNTHETIC",
                    "last_divergence_delta": 0.0,
                    "last_probe_timestamp": None
                }, f)

    def _get_state(self) -> Dict[str, Any]:
        with open(self.state_path, "r") as f:
            return json.load(f)

    def _save_state(self, state: Dict[str, Any]):
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def probe(self, primitive_id: str = "EXT_TELEMETRY_QUERY", endpoint: str = "https://httpbin.org/get") -> Dict[str, Any]:
        """
        Performs a dual-track probe to detect environment divergence and network parity.
        """
        state = self._get_state()
        
        # 1. Synthetic track (SSE)
        synth_res = self.sse.mock_response(primitive_id)
        synth_val = float(synth_res["data"].get("node_sync_latency", "0").replace("ms", "")) if "data" in synth_res else 0.0

        # 2. Live track (S-Bridge)
        live_res = self.bridge.call("GET", endpoint)
        
        # Evaluation logic
        is_live_success = (live_res["status"] == "SUCCESS")
        live_val = 0.0
        if is_live_success:
            try:
                data = live_res.get("data", {})
                if isinstance(data, dict):
                    # Use 'node_sync_latency' if present (mirror mode), 
                    # otherwise treat as 0.0 to allow a 'baseline' parity.
                    live_val = float(data.get("node_sync_latency", "0").replace("ms", ""))
                else:
                    live_val = 0.0
            except Exception:
                live_val = 0.0

        # Calculate Divergence Delta
        delta = abs(live_val - synth_val)
        state["last_divergence_delta"] = delta
        state["last_probe_timestamp"] = datetime.utcnow().isoformat() + "Z"

        # SENTRY TRIGGER: Divergence detected during live success
        if is_live_success and delta > 2.0: 
            signal = emit_signal(
                "SIG_S-SENTRY", 
                f"DIVERGENCE_DELTA: {delta:.2f}", 
                {"primitive": primitive_id, "live": live_val, "synth": synth_val}
            )
            print(signal)

        # PARITY TRACKING
        if is_live_success:
            state["consecutive_successes"] += 1
            if state["consecutive_successes"] >= 3 and state["parity_status"] != "PARITY_CONFIRMED":
                state["parity_status"] = "PARITY_CONFIRMED"
                signal = emit_signal(
                    "SIG_S-PIVOT", 
                    "STATE: NETWORK_PARITY_RESTORED", 
                    {"success_count": state["consecutive_successes"]}
                )
                print(signal)
        else:
            state["consecutive_successes"] = 0
            state["parity_status"] = "SYNTHETIC"

        self._save_state(state)

        return {
            "live_status": "SUCCESS" if is_live_success else "FAILED",
            "parity_status": state["parity_status"],
            "delta": delta,
            "consecutive_successes": state["consecutive_successes"]
        }

if __name__ == "__main__":
    probe = SovereignProbe()
    print(json.dumps(probe.probe(), indent=2))
