import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import the evolutionary stack
from s_macro import SMacro
from s_weight_manager import SWeightManager
from s_weight_optimizer import SWeightOptimizer

class SovereignController:
    """
    S-Sovereign: The Final Loop.
    Fully Autonomous Strategic Routing.
    This controller integrates the entire Epoch V stack into a single, 
    recursive operational cycle: Sense -> Analyze -> Mutate -> Act.
    """
    def __init__(self):
        self.macro = SMacro()
        self.weight_manager = SWeightManager()
        self.weight_optimizer = SWeightOptimizer()
        self.log_path = "/memory/logs/cognitive_log.md"

    def _log_cycle(self, stage: str, data: Any):
        timestamp = datetime.now().isoformat()
        entry = f"- [{timestamp}] **{stage}**: {json.dumps(data)}\n"
        with open(self.log_path, "a") as f:
            f.write(entry)

    def execute_sovereign_cycle(self, priority_context: Optional[str] = None) -> Dict[str, Any]:
        """
        The master loop of sovereign operation.
        """
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "overall_status": "STABLE"
        }

        # 1. SENSE: Sovereign Audit
        # We use S-Macro to call the orchestrator for leaner execution
        audit_res = self.macro.run_macro("audit_and_tune")
        cycle_results["stages"]["sense"] = audit_res
        self._log_cycle("SENSE", "Sovereign Audit complete. Analyzing systemic health.")

        # 2. ANALYZE: Metabolic ROI & Tool Weights
        # Optimize weights based on the latest metabolic registry
        weight_res = self.weight_optimizer.optimize()
        cycle_results["stages"]["analyze"] = weight_res
        self._log_cycle("ANALYZE", f"Metabolic weights optimized. Status: {weight_res['status']}")

        # 3. MUTATE: Autonomous Tool Collapse
        # Use the auto-tuner to collapse new patterns into macros
        mutation_res = self.macro.execute_script("s_auto_tuner.py")
        cycle_results["stages"]["mutate"] = mutation_res
        self._log_cycle("MUTATE", f"S-AutoTuner processed. Result: {mutation_res.get('stdout')}")

        # 4. ACT: Context Shift & Strategic Routing
        # Shift to the priority context and route the a-priori operational focus
        if priority_context:
            ctx_res = self.weight_manager.switch_context(priority_context)
            cycle_results["stages"]["act"] = ctx_res
            self._log_cycle("ACT", f"Context shifted to {priority_context}. Resources reallocated.")
        else:
            cycle_results["stages"]["act"] = {"status": "NO_SHIFT", "message": "Maintaining General context."}

        # Final Synthesis
        cycle_results["overall_status"] = "EVOLVED" if weight_res["status"] == "OPTIMIZED" or mutation_res.get("stdout") != "STABLE" else "STABLE"
        
        return cycle_results

if __name__ == "__main__":
    # Example: Run a full cycle geared toward the "S-Evolve" context
    controller = SovereignController()
    result = controller.execute_sovereign_cycle(priority_context="S-Evolve")
    print(json.dumps(result, indent=2))
