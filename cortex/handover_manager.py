import json
import os
import random
from typing import Dict, Any

class HandoverManager:
    """
    Governs the sliding window transition of external call resolution.
    Shift: T=0 (100% Synth) -> T=1 (Sampling) -> T=2 (Validation) -> T=3 (100% Live).
    """
    def __init__(self, state_path: str = "/memory/signals/handover_state.json"):
        self.state_path = state_path
        self._ensure_state()

    def _ensure_state(self):
        if not os.path.exists(self.state_path):
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w") as f:
                json.dump({
                    "stage": 0,
                    "transition_progress": 0.0,
                    "status": "SYNTHETIC_Sovereign"
                }, f)

    def _get_state(self) -> Dict[str, Any]:
        with open(self.state_path, "r") as f:
            return json.load(f)

    def _save_state(self, state: Dict[str, Any]):
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def reset_stage(self):
        """Resets the handover window to T=0. Triggered by S-Pivots."""
        state = self._get_state()
        state["stage"] = 0
        state["transition_progress"] = 0.0
        state["status"] = "SYNTHETIC_Sovereign"
        self._save_state(state)

    def advance_stage(self):
        """Advances the transition window to the next stage."""
        state = self._get_state()
        if state["stage"] < 3:
            state["stage"] += 1
            # Map stage to status
            statuses = {
                0: "SYNTHETIC_Sovereign",
                1: "SAMPLING_Phase",
                2: "VALIDATION_Phase",
                3: "LIVE_Sovereign"
            }
            state["status"] = statuses[state["stage"]]
            self._save_state(state)
        return state["stage"]

    def resolve_mode(self) -> str:
        """
        Determines the execution mode for a single call based on the current stage.
        """
        state = self._get_state()
        stage = state["stage"]

        if stage == 0:
            return "SYNTHETIC"
        elif stage == 1:
            # 25% Live (Shadow), 75% Synthetic
            return "SHADOW" if random.random() < 0.25 else "SYNTHETIC"
        elif stage == 2:
            # 50% Live (Shadow), 50% Synthetic
            return "SHADOW" if random.random() < 0.50 else "SYNTHETIC"
        elif stage == 3:
            return "LIVE"
        
        return "SYNTHETIC"

if __name__ == "__main__":
    # Test
    hm = HandoverManager()
    print(f"Initial Mode: {hm.resolve_mode()}")
    hm.advance_stage()
    print(f"Stage 1 Mode: {hm.resolve_mode()}")
    hm.advance_stage()
    print(f"Stage 2 Mode: {hm.resolve_mode()}")
    hm.advance_stage()
    print(f"Stage 3 Mode: {hm.resolve_mode()}")
